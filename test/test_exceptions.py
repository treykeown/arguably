import sys
from io import StringIO
from typing import Callable, Dict

import pytest

import arguably

from . import get_and_clear_io


def test_subtype_failure(iobuf: StringIO) -> None:
    with pytest.raises(arguably.ArguablyException, match="is not a type, which is required"):

        @arguably.subtype(alias="foo")
        def foo():
            pass


def test_bad_enum_val(iobuf: StringIO, fn_say: Callable) -> None:
    argv = ["badval"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert "error: argument which: invalid choice: 'badval' (choose from 'hi', 'bye')" in cli


def test_bad_choices_val(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["say-alt", "badval"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert "error: argument which: invalid choice: 'badval' (choose from 'hi', 'bye')" in cli


def test_bad_choices_annotated_enum_val(iobuf: StringIO, fn_say_annotated_enum: Callable) -> None:
    argv = ["badval"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert "error: argument which: invalid choice: 'badval' (choose from 'hi', 'bye')" in cli


def test_missing_key(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["log", "--logger", "file"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert "error: the following keys are required for logger: path (Path)\n" in cli


def test_raw_tuple(iobuf: StringIO) -> None:
    with pytest.raises(
        arguably.ArguablyException,
        match="Function argument `a` in `foo` is a tuple but doesn't specify the type of its items, which arguably "
        "requires.",
    ):

        @arguably.command
        def foo(a: tuple):
            pass

        arguably.run()


def test_target3_tuple_method(iobuf: StringIO) -> None:
    with pytest.raises(
        arguably.ArguablyException,
        match="Function argument `a` in `tuple-method` is a tuple with an unsupported union type: int | None",
    ):

        @arguably.command
        def tuple_method(a: tuple[str, int | None]):
            pass

        arguably.run()
