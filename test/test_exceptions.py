import sys
from io import StringIO
from typing import Callable

import pytest

import noarg
from . import get_and_clear_io


def test_subtype_failure(iobuf: StringIO) -> None:
    with pytest.raises(noarg.NoArgException, match="is not a type, which is required"):

        @noarg.subtype(alias="foo")
        def foo():
            pass


def test_bad_enum_val(iobuf: StringIO, fn_say: Callable) -> None:
    argv = ["badval"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        noarg.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert "error: argument which: invalid choice: 'badval' (choose from 'hi', 'bye')" in cli


def test_bad_choices_val(iobuf: StringIO, scope_annotated: dict[str, Callable]) -> None:
    argv = ["say-alt", "badval"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        noarg.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert "error: argument which: invalid choice: 'badval' (choose from 'hi', 'bye')" in cli


def test_bad_choices_annotated_enum_val(iobuf: StringIO, fn_say_annotated_enum: Callable) -> None:
    argv = ["badval"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        noarg.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert "error: argument which: invalid choice: 'badval' (choose from 'hi', 'bye')" in cli


def test_missing_key(iobuf: StringIO, scope_annotated: dict[str, Callable]) -> None:
    argv = ["log", "--logger", "file"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        noarg.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert "error: the following keys are required for logger: path (Path)\n" in cli
