import sys
from io import StringIO
from typing import Callable, Dict

import pytest

import arguably
from . import get_and_clear_io, run_cli_and_manual


def test_help(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, name="advanced")
    cli = get_and_clear_io(iobuf)

    assert cli.startswith("usage: advanced [-h] [--loud] command ...\n")
    assert "add          adds a bunch of numbers together" in cli
    assert "give         give something" in cli
    assert "hey-you (h)  says hello to you" in cli
    assert "  --loud         make it loud (default: False)" in cli


def test_hey_you_help(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["h", "-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, name="advanced")
    cli = get_and_clear_io(iobuf)

    assert cli.startswith("usage: advanced hey-you [-h] name")
    assert "says hello to you" in cli
    assert "name        your name" in cli


def test_hey_you(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["hey-you", "John"]
    args = ["John"]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["hey_you"], argv, args, kwargs)

    assert "> hey-you\n" in cli
    assert cli == manual


def test_give(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["give"]
    args = []
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["give"], argv, args, kwargs)

    assert "> give\n" in cli
    assert "give is main\n" in cli
    assert cli == manual


def test_give_zen(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["give", "zen", "--rotten"]
    args = []
    kwargs = dict(rotten=True)

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["give__zen"], argv, args, kwargs)

    assert "> give zen\n" in cli
    assert "give zen rotten\n" in cli
    assert cli == manual


def test_give_zen_ancestor(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["give", "--slowly", "zen", "--rotten"]
    args = []
    kwargs = dict(rotten=True)

    scope_advanced["__root__"]()
    scope_advanced["give"](slowly=True)
    cli, manual = run_cli_and_manual(iobuf, scope_advanced["give__zen"], argv, args, kwargs, dict(call_ancestors=True))

    cli_lines = list(sorted(cli.split("\n")))
    manual_lines = list(sorted(manual.split("\n")))
    manual_lines.remove("give is main")

    assert "> give\n" in cli
    assert "> give zen\n" in cli
    assert "give zen rotten\n" in cli
    assert cli_lines == manual_lines


def test_do__a_dance(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["do", "a-dance"]
    args = []
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["do__a_dance"], argv, args, kwargs)

    assert "> do a-dance\n" in cli
    assert cli == manual


def test_add(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["add", "1", "1", "2", "3", "--coords", "10,20,30"]
    args = [1, 1, 2, 3]
    kwargs = dict(coords=(10, 20, 30))

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["add"], argv, args, kwargs)

    assert "> add\n" in cli
    assert "add sum: 7\n" in cli
    assert "add coords: 17, 27, 37\n" in cli
    assert cli == manual


def test_add_help(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["add", "-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, name="advanced")
    cli = get_and_clear_io(iobuf)

    assert cli.startswith("usage: advanced add [-h] [-c X,Y,Z] NUMS [NUMS ...]\n")
    assert "adds a bunch of numbers together\n" in cli
    assert "  NUMS                the numbers NUMS to add\n" in cli
    assert "  -c, --coords X,Y,Z  coordinates X,Y,Z updated with the sum (default: None)\n" in cli


def test_mixed_tuple(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["mixed-tuple", "foo,10,123.45"]
    args = [("foo", 10, 123.45)]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["mixed_tuple"], argv, args, kwargs)

    assert "> mixed-tuple\n" in cli
    assert "'foo', 10, 123.45\n" in cli
    assert cli == manual


def test_mixed_tuple_help(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["mixed-tuple", "-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, name="advanced", show_types=True)
    cli = get_and_clear_io(iobuf)

    assert cli.startswith("usage: advanced mixed-tuple [-h] val,val,val\n")
    assert "  val,val,val  the values (type: str,int,float)" in cli
