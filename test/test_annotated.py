import sys
from io import StringIO
from pathlib import Path
from typing import Callable, Dict

import pytest

import arguably
from . import run_cli_and_manual, get_and_clear_io


def test_log(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["log", "--logger", "file,path=foo.txt"]
    args = []
    kwargs = dict(logger=scope_annotated["FileLogger"](path=Path("foo.txt")))

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["log"], argv, args, kwargs)

    assert "~file foo.txt: Howdy, there!\n" in cli
    assert cli == manual


def test_multi_log(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["multi-log", "--logger", "file,path=foo.txt", "--logger", "term"]
    args = []
    kwargs = dict(logger=[scope_annotated["FileLogger"](path=Path("foo.txt")), scope_annotated["TerminalLogger"]()])

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["multi_log"], argv, args, kwargs)

    assert "~file foo.txt: Howdy, there!\n" in cli
    assert "~term: Howdy, there!\n" in cli
    assert cli == manual


def test_dataclass(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["dataclass", "foo=10,bar=test"]
    args = [scope_annotated["Complex"](10, "test")]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["dataclass"], argv, args, kwargs)

    assert "Complex(foo=10, bar='test')\n" in cli
    assert cli == manual


def test_explain_none(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["explain"]
    args = []
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["explain"], argv, args, kwargs)

    assert "verbosity: 0\n" in cli
    assert cli == manual


def test_explain(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["explain", "-vvv", "-v"]
    args = []
    kwargs = dict(verbose=4)

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["explain"], argv, args, kwargs)

    assert "verbosity: 4\n" in cli
    assert cli == manual


def test_high_five_required(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["high-five"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, name="advanced")
    cli = get_and_clear_io(iobuf)
    print(cli)

    assert cli.startswith("usage: advanced high-five [-h] people [people ...]")
    assert "error: the following arguments are required: people\n" in cli


def test_email_alt(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["email-alt", "john@doe.co", 'test@example.com,foo@bar.biz,"Last, First" <first@last.name>']
    args = ["john@doe.co"]
    kwargs = dict(cc=["test@example.com", "foo@bar.biz", '"Last, First" <first@last.name>'], bcc=[])

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["email_alt"], argv, args, kwargs)

    assert cli == manual


def test_email(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = [
        "email",
        "john@doe.co",
        "abc@def.co",
        "ghi@jkl.net",
        "--cc",
        "asdf@gmail.biz",
        "--cc",
        "test@example.com,'foo@bar.biz','Last, First' <first@last.name>",
        "--bcc",
        "-",
    ]
    args = ["john@doe.co", "abc@def.co", "ghi@jkl.net"]
    kwargs = dict(cc=["asdf@gmail.biz", "test@example.com", "foo@bar.biz", "'Last, First' <first@last.name>"], bcc=[])

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["email"], argv, args, kwargs)

    assert "bcc is none" not in cli
    assert cli == manual


def test_say_alt(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["say-alt", "hi"]
    args = ["hi"]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["say_alt"], argv, args, kwargs)

    assert "which: hi\n" in cli
    assert cli == manual


def test_goodbye_none(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["goodbye"]
    args = []
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["goodbye"], argv, args, kwargs)

    assert "path: None\n" in cli
    assert cli == manual


def test_goodbye_flag(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["goodbye", "--path"]

    sys.argv.extend(argv)
    arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert "path: ~/goodbye.log\n" in cli


def test_goodbye_option(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["goodbye", "--path", "~/alt.txt"]
    args = []
    kwargs = dict(path="~/alt.txt")

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["goodbye"], argv, args, kwargs)

    assert "path: ~/alt.txt\n" in cli
    assert cli == manual


def test_handle_it(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["handle-it", "5"]
    args = [25]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_annotated["handle_it"], argv, args, kwargs)

    assert "squared: 25\n" in cli
    assert cli == manual


def test_say_alt_failure(iobuf: StringIO, scope_annotated: Dict[str, Callable]) -> None:
    argv = ["say-alt", "howdy"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, name="advanced")
    cli = get_and_clear_io(iobuf)

    assert cli.startswith("usage: advanced say-alt [-h] {hi,bye}\n")
    assert "error: argument which: invalid choice: 'howdy' (choose from 'hi', 'bye')\n" in cli
