from __future__ import annotations

import ast
import asyncio
import enum
import functools
import importlib.util
import inspect
import logging
import math
import multiprocessing
import re
import sys
import time
import warnings
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Callable, cast, Any, Union, Optional, List, Dict, Type, Tuple, TextIO

from docstring_parser import parse as docparse

# Annotated is 3.9 and up
if sys.version_info >= (3, 9):
    from typing import Annotated, get_type_hints, get_args, get_origin  # noqa
else:  # pragma: no cover
    from typing_extensions import Annotated, get_type_hints, get_args, get_origin  # noqa

# UnionType is the new type for the `A | B` type syntax, which is 3.10 and up
if sys.version_info >= (3, 10):
    from types import UnionType  # noqa
else:  # pragma: no cover

    class UnionType:
        """Stub this out, we only use it for issubclass() checks"""


logger = logging.getLogger("arguably")


def is_async_callable(obj: Any) -> bool:
    """Checks if an object is an async callable - https://stackoverflow.com/a/72682939"""
    while isinstance(obj, functools.partial):
        obj = obj.func
    return asyncio.iscoroutinefunction(obj) or (callable(obj) and asyncio.iscoroutinefunction(obj.__call__))


def split_unquoted(unsplit: str, delimeter: str, limit: Union[int, float] = math.inf) -> List[str]:
    """Splits text at a delimiter, as long as that delimiter is not quoted (either single ' or double quotes ")."""
    assert len(delimeter) == 1
    assert limit > 0
    result = list()
    quote_char = None
    accumulator: List[str] = list()
    for char in unsplit:
        if char == delimeter and quote_char is None and limit > 0:
            result.append("".join(accumulator))
            accumulator.clear()
            limit -= 1
            continue
        elif char == "'":
            if quote_char is None:
                quote_char = "'"
            elif quote_char == "'":
                quote_char = None
        elif char == '"':
            if quote_char is None:
                quote_char = '"'
            elif quote_char == '"':
                quote_char = None
        accumulator.append(char)
    result.append("".join(accumulator))
    accumulator.clear()
    return result


class NoDefault:
    """Indicator that there is no default value for a parameter. Necessary because None can be the default value."""


def unwrap_quotes(qs: str) -> str:
    """Removes quotes wrapping a string - they must be matching, and also be the first and last character"""
    if (qs.startswith('"') and qs.endswith('"')) or (qs.startswith("'") and qs.endswith("'")):
        return qs[1:-1]
    return qs


def get_ancestors(command_name: str) -> List[str]:
    """
    List all ancestors for a given command. For example, `foo bar bat` yeilds a list with:
      * `__root__`
      * `__root__ foo`
      * `__root__ foo bar`

    Note that `__root__` is always an implicit ancestor.
    """
    if command_name == "__root__":
        return []
    tokens = command_name.split(" ")
    return ["__root__"] + [" ".join(tokens[: i + 1]) for i in range(len(tokens))][:-1]


def normalize_name(name: str, spaces: bool = True) -> str:
    """
    Normalizes a name. It's converted to lowercase, leading and trailing `_` are stripped, and `_` is converted to `-`.
    If `spaces` is true, it also converts `__` to a single space ` `.
    """
    result = name.lower().strip("_")
    if spaces:
        result = result.replace("__", " ")
    result = result.replace("_", "-")
    if len(result.strip("- ")) == 0:
        raise ArguablyException(f"Cannot normalize name `{name}` - cannot just be underscores and dashes.")
    return result


@dataclass
class EnumFlagInfo:
    """Used similarly to _CommandArg, but for entries in an `enum.Flag`."""

    option: Union[Tuple[str], Tuple[str, str]]
    cli_arg_name: str
    value: Any
    description: str


def get_enum_member_docs(enum_class: Type[enum.Enum]) -> Dict[str, str]:
    """Extracts docstrings for enum members similar to PEP-224, which has become a pseudo-standard supported by a lot of
    tooling"""
    parsed = ast.parse(inspect.getsource(enum_class))
    assert len(parsed.body) == 1

    classdef = parsed.body[0]
    assert isinstance(classdef, ast.ClassDef)

    # Search for a string expression following an assignment
    prev = None
    result: Dict[str, str] = dict()
    for item in classdef.body:
        if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
            if isinstance(prev, ast.Assign) and len(prev.targets) == 1 and isinstance(prev.targets[0], ast.Name):
                result[cast(ast.Name, prev.targets[0]).id] = item.value.value
        prev = item

    return result


def info_for_flags(cli_arg_name: str, flag_class: Type[enum.Flag]) -> List[EnumFlagInfo]:
    """Generates a list of `_EnumFlagInfo` corresponding to all flags in an `enum.Flag`."""
    result = list()
    docs = docparse(flag_class.__doc__ or "")
    enum_member_docs = get_enum_member_docs(flag_class)
    for item in flag_class:
        options = [f"--{normalize_name(cast(str, item.name))}"]
        arg_description = ""

        # `docstring_parser` does not specially parse out attibutes declared in the docstring - we have to do that
        # ourselves here.
        found = False
        for doc_item in docs.meta:
            assert len(doc_item.args) >= 2
            doc_item_type, doc_item_name = doc_item.args[0], doc_item.args[-1]
            if item.name != doc_item_name:
                continue
            if doc_item_type not in ["var", "cvar", "attribute", "attr"]:
                continue
            arg_description = doc_item.description or ""

            found = True
            break

        if not found and item.name in enum_member_docs:
            # noinspection PyTypeChecker
            arg_description = enum_member_docs[item.name]

        # Extract the alias from the docstring for the flag item
        if alias_match := re.match(r"^\[-([a-zA-Z0-9])] ", arg_description):
            arg_description = arg_description[len(alias_match.group(0)) :]
            options.insert(0, f"-{alias_match.group(1)}")

        result.append(
            EnumFlagInfo(cast(Union[Tuple[str], Tuple[str, str]], tuple(options)), cli_arg_name, item, arg_description)
        )
    return result


########################################################################################################################
# For __main__


class RedirectedIO(StringIO):
    def __init__(self, pipe: Any) -> None:
        super().__init__()
        self.pipe = pipe

    def write(self, s: str) -> int:
        self.pipe.send(s)
        return len(s)


def capture_stdout_stderr(stdout_writer: Any, stderr_writer: Any, target: Callable, args: Tuple[Any, ...]) -> None:
    sys.stdout = RedirectedIO(stdout_writer)
    sys.stderr = RedirectedIO(stderr_writer)

    target(*args)

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__


def io_redirector(proc: multiprocessing.Process, pipe: Any, file: TextIO) -> None:
    while True:
        try:
            recv = pipe.recv().strip()
            if recv:
                print(recv, file=file)
        except OSError:
            if not proc.is_alive():
                break
            time.sleep(0.05)
        except EOFError:
            break


def run_redirected_io(mp_ctx: multiprocessing.context.SpawnContext, target: Callable, args: Tuple[Any, ...]) -> None:
    """Redirects the subprocess's stdout/stderr back to THIS process's stdout/stderr"""
    from threading import Thread

    # Set up multiprocessing so we can launch a new process to load the file
    # We redirect stdout and stderr back to us and print in threads
    stdout_reader, stdout_writer = mp_ctx.Pipe()
    stderr_reader, stderr_writer = mp_ctx.Pipe()

    proc = mp_ctx.Process(target=capture_stdout_stderr, args=(stdout_writer, stderr_writer, target, args))

    # Run the external process
    proc.start()
    Thread(target=io_redirector, args=(proc, stdout_reader, sys.stdout)).start()
    Thread(target=io_redirector, args=(proc, stderr_reader, sys.stderr)).start()
    proc.join()

    stderr_reader.close()
    stderr_writer.close()


@dataclass
class LoadAndRunResult:
    """Result from load_and_run"""

    error: Optional[str] = None
    exception: Optional[BaseException] = None


@dataclass
class ArgSpec:
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


def get_parser_name(prog_name: str) -> str:
    nice_name = prog_name.partition(" ")[2]
    if nice_name == "":
        return "__root__"
    return nice_name


def log_args(logger_fn: Callable, msg: str, fn_name: str, *args: Any, **kwargs: Any) -> ArgSpec:
    args_str = ", ".join(repr(a) for a in args)
    kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
    if len(args_str) == 0 or len(kwargs_str) == 0:
        full_arg_string = f"{args_str}{kwargs_str}"
    else:
        full_arg_string = f"{args_str}, {kwargs_str}"
    logger_fn(f"{msg}{fn_name}({full_arg_string})")
    return ArgSpec(args, kwargs)


def func_info(function: Callable) -> Optional[Tuple[str, int]]:
    source_file = inspect.getsourcefile(function)
    if source_file is None:
        return None

    # Skip lines before the `def`. Should be cleaned up in the future.
    source_lines, line_number = inspect.getsourcelines(function)
    for line in source_lines:
        if "def " not in line:
            line_number += 1
        break

    return source_file, line_number


def warn(message: str, function: Optional[Callable] = None) -> None:
    """Provide a warning. We avoid using logging, since we're just a library, so we issue through `warnings`."""

    if function is not None:
        info = func_info(function)
        if info is not None:
            source_file, source_file_line = info
            warnings.warn_explicit(
                message,
                ArguablyWarning,
                source_file,
                source_file_line,
            )
            return

    warnings.warn(message, ArguablyWarning)
    return


def get_callable_methods(cls: type) -> List[Callable]:
    """
    Gets all the callable methods from a function - __init__, classmethods, and staticmethods. Skips abstractmethods.
    """
    callable_methods = []

    for name, method in vars(cls).items():
        if (name.startswith("__") and name.endswith("__")) or inspect.isabstract(method):
            continue
        if isinstance(method, staticmethod) or isinstance(method, classmethod):
            callable_methods.append(getattr(cls, name))

    return callable_methods


def load_and_run_inner(file: Path, *args: str, debug: bool, no_warn: bool) -> LoadAndRunResult:
    import arguably

    if debug:
        logging.basicConfig(level=logging.DEBUG, format="%(pathname)s:%(lineno)d: %(message)s")

    if no_warn:
        warnings.filterwarnings(action="ignore", category=arguably.ArguablyWarning)

    # Load the specified file
    spec = importlib.util.spec_from_file_location("_arguably_imported", str(file))
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_arguably_imported"] = module
    spec.loader.exec_module(module)

    # Collect all callables (classes and functions)
    callables = [item for item in vars(module).values() if callable(item)]

    functions = list()
    classes = list()
    for callable_ in callables:
        if isinstance(callable_, type):
            classes.append(callable_)
        else:
            functions.append(callable_)

    # For classmethods and staticmethods, we prepend the class name when we call `arguably.command`. Keep track of the
    # real name here so we can revert it after
    real_names: Dict[Any, str] = dict()

    # Add classmethods and staticmethods
    for cls in classes:
        # Add the initializer for the class itself, if it's not abstract
        if not inspect.isabstract(cls):
            functions.append(cls)

        # Add classmethods and staticmethods
        for callable_method in get_callable_methods(cls):
            if inspect.ismethod(callable_method):
                # We have to set through .__func__ for the bound @classmethod
                callable_method = cast(classmethod, callable_method)  # type: ignore[assignment]
                real_names[callable_method] = callable_method.__name__
                callable_method.__func__.__name__ = f"{cls.__name__}.{callable_method.__name__}"
            else:
                real_names[callable_method] = callable_method.__name__
                callable_method.__name__ = f"{cls.__name__}.{callable_method.__name__}"
            functions.append(callable_method)

    arguably._context.context.reset()

    # Add all functions to arguably
    for function in functions:
        try:
            # Heuristic for determining what is close enough to a class or function
            inspect.signature(function)
            get_type_hints(function, include_extras=True)
        except TypeError:
            continue

        try:
            arguably.command(function)
        except Exception as e:
            warn(f"Unable to add function {function.__name__}: {str(e)}", function)
            continue

        # If it's a classmethod or staticmethod, revert the name
        if function in real_names:
            if inspect.ismethod(function):
                function.__func__.__name__ = real_names[function]
            else:
                function.__name__ = real_names[function]

    sys.argv.extend(args)

    # Run and return success
    arguably.run(name=file.stem, always_subcommand=True, strict=False)
    return LoadAndRunResult()


def load_and_run(results: multiprocessing.Queue, file: Path, argv: List[str], debug: bool, no_warn: bool) -> None:
    """Load the specified file, register all callable top-level functions, classmethods, and staticmethods, then run"""
    try:
        results.put(load_and_run_inner(file, *argv, debug=debug, no_warn=no_warn))
    except BaseException as e:
        results.put(LoadAndRunResult(exception=e))


########################################################################################################################
# Exposed for API


class ArguablyException(Exception):
    """
    Raised when a decorated function is incorrectly set up in some way. Will *not* be raised when a user provides
    incorrect input to the CLI.

    Examples:
        ```python
        #!/usr/bin/env python3
        import arguably

        @arguably.command
        def example(collision_, _collision):
            print("You should never see this")

        if __name__ == "__main__":
            arguably.run()
        ```

        ```console
        user@machine:~$ python3 arguably-exception.py
        Traceback (most recent call last):
          File ".../arguably/etc/scripts/api-examples/arguably-exception.py", line 9, in <module>
            arguably.run()
          File ".../arguably/arguably/_context.py", line 706, in run
            cmd = self._process_decorator_info(command_decorator_info)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          File ".../arguably/arguably/_context.py", line 284, in _process_decorator_info
            return Command(
                   ^^^^^^^^
          File "<string>", line 9, in __init__
          File ".../arguably/arguably/_commands.py", line 214, in __post_init__
            raise util.ArguablyException(
        arguably._util.ArguablyException: Function parameter `_collision` in `example` conflicts with `collision_`, both
        names simplify to `collision`
        ```
    """


class ArguablyWarning(UserWarning):
    """
    Emitted when a decorated function is incorrectly set up in some way, but arguably can continue. Will *not* be raised
    when a user provides incorrect input to the CLI.

    Note that this is a warning - it is used with `warnings.warn`.

    Examples:
        ```python
        def example_failed(collision_, _collision):
            print("You should never see this")

        def example_ok():
            print("All good")
        ```

        ```console
        user@machine:~$ python3 -m arguably-warn.py -h
        .../arguably/etc/scripts/api-examples/arguably-warn.py:1: ArguablyWarning: Unable to add function
        example_failed: Function parameter `_collision` in `example-failed` conflicts with `collision_`, both names
        simplify to `collision`
          def example_failed(collision_, _collision):
        usage: arguably-warn [-h] command ...

        positional arguments:
          command
            example-ok

        options:
          -h, --help    show this help message and exit
        ```
    """
