import importlib.util
import inspect
import logging
import multiprocessing
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, cast, Callable

import arguably


logger = logging.getLogger("arguably")


@dataclass
class LoadAndRunResult:
    """Result from load_and_run"""

    error: Optional[str] = None
    exception: Optional[BaseException] = None


def warn(message: str, function: Callable) -> None:
    """Provide a warning. We avoid using logging, since we're just a library, so we issue through `warnings`."""

    source_file = inspect.getsourcefile(function)
    if source_file is None:
        warnings.warn(message, arguably.ArguablyWarning)
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
        arguably.ArguablyWarning,
        source_file,
        line_number,
    )


def _get_callable_methods(cls: type) -> List[Callable]:
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


def _load_and_run_inner(file: Path, *args: str, debug: bool) -> LoadAndRunResult:
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
        for callable_method in _get_callable_methods(cls):
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
        results.put(_load_and_run_inner(file, *argv, debug=debug))
    except BaseException as e:
        results.put(LoadAndRunResult(exception=e))
