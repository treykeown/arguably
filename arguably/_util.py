from __future__ import annotations

import ast
import enum
import importlib.util
import inspect
import logging
import math
import multiprocessing
import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, cast, Any, Collection, Union, Optional, List, Dict, Type, Tuple

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


def find_alias(used_aliases: Collection[str], name: str) -> Optional[str]:
    """
    Simple algorithm for automatically finding an alias for a parameter. There are better ways, but this works for now.
    Iterates over each character in a parameter, tries both lowercase and uppercase variants. Returns the first one
    found that isn't in used_aliases.
    """
    for char in name:
        for transform in [lambda s: s.lower(), lambda s: s.upper()]:
            alias = transform(char)
            assert len(alias) == 1, f"One character became more than one: `{char}` -> `{alias}`"
            if alias not in used_aliases:
                return alias
    return None


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
    return ["__root__"] + ["".join(tokens[: i + 1]) for i in range(len(tokens))][:-1]


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


@dataclass
class LoadAndRunResult:
    """Result from load_and_run"""

    error: Optional[str] = None
    exception: Optional[BaseException] = None


@dataclass
class ArgSpec:
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


def log_args(logger_fn: Callable, msg: str, fn_name: str, *args: Any, **kwargs: Any) -> ArgSpec:
    args_str = ", ".join(repr(a) for a in args)
    kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
    if len(args_str) == 0 or len(kwargs_str) == 0:
        full_arg_string = f"{args_str}{kwargs_str}"
    else:
        full_arg_string = f"{args_str}, {kwargs_str}"
    logger_fn(f"{msg}{fn_name}({full_arg_string})")
    return ArgSpec(args, kwargs)


def warn(message: str, function: Callable) -> None:
    """Provide a warning. We avoid using logging, since we're just a library, so we issue through `warnings`."""

    source_file = inspect.getsourcefile(function)
    if source_file is None:
        warnings.warn(message, ArguablyWarning)
        return

    # Skip lines before the `def`. Should be cleaned up in the future.
    source_lines, line_number = inspect.getsourcelines(function)
    for line in source_lines:
        if "def " not in line:
            line_number += 1
        break

    # Issue the warning
    warnings.warn_explicit(
        message,
        ArguablyWarning,
        source_file,
        line_number,
    )


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


def load_and_run_inner(file: Path, *args: str, debug: bool) -> LoadAndRunResult:
    import arguably

    if debug:
        logging.basicConfig(level=logging.DEBUG, format="%(pathname)s:%(lineno)d: %(message)s")

    # Load the specified file
    spec = importlib.util.spec_from_file_location("_arguably_imported", str(file))
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
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

    # Add all functions to arguably
    for function in functions:
        try:
            arguably.command(function)
        except arguably.ArguablyException as e:
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
    arguably.run(name=file.stem, always_subcommand=True, show_types=True, show_defaults=True)
    return LoadAndRunResult()


def load_and_run(results: multiprocessing.Queue, file: Path, argv: List[str], debug: bool) -> None:
    """Load the specified file, register all callable top-level functions, classmethods, and staticmethods, then run"""
    try:
        results.put(load_and_run_inner(file, *argv, debug=debug))
    except BaseException as e:
        results.put(LoadAndRunResult(exception=e))


########################################################################################################################
# Exposed for API


class ArguablyWarning(UserWarning):
    """Raised when a decorated function is incorrectly set up in some way, but arguably can continue"""


class ArguablyException(Exception):
    """Raised when a decorated function is incorrectly set up in some way"""
