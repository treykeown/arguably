import sys
from io import StringIO
from typing import Callable

import pytest

import arguably
from . import get_and_clear_io, run_cli_and_manual


########################################################################################################################
# no commands


def test_no_commands(iobuf: StringIO) -> None:
    with pytest.raises(arguably.ArguablyException, match="At least one command is required"):
        arguably.run(output=iobuf)


########################################################################################################################
# basic()


def test_basic_help(iobuf: StringIO, fn_basic: Callable) -> None:
    argv = ["-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.startswith(f"usage: {test_basic_help.__name__} [-h]\n")
    assert cli.endswith("show this help message and exit\n")


def test_basic_no_args(iobuf: StringIO, fn_basic: Callable) -> None:
    argv = []
    args = []
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, fn_basic, argv, args, kwargs)

    assert cli == "basic\n"
    assert cli == manual


def test_basic_too_many_args(iobuf: StringIO, fn_basic: Callable) -> None:
    argv = ["foobar"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.endswith("error: unrecognized arguments: foobar\n")


def test_basic_unknown_opt(iobuf: StringIO, fn_basic: Callable) -> None:
    argv = ["--foo", "bar"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.endswith("error: unrecognized arguments: --foo bar\n")


########################################################################################################################
# hello()


def test_hello_no_args(iobuf: StringIO, fn_hello: Callable) -> None:
    argv = []

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.endswith("error: the following arguments are required: name\n")


def test_hello_normal(iobuf: StringIO, fn_hello: Callable) -> None:
    argv = ["John"]
    args = ["John"]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, fn_hello, argv, args, kwargs)

    assert cli == manual


def test_hello_normal_optional(iobuf: StringIO, fn_hello: Callable) -> None:
    argv = ["John", "25"]
    args = ["John", 25]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, fn_hello, argv, args, kwargs)

    assert cli == manual


def test_hello_wrong_type(iobuf: StringIO, fn_hello: Callable) -> None:
    argv = ["John", "Doe"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.endswith("error: argument age: invalid int value: 'Doe'\n")


def test_hello_negative(iobuf: StringIO, fn_hello: Callable) -> None:
    argv = ["John", "-5"]
    args = ["John", -5]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, fn_hello, argv, args, kwargs)

    assert cli == manual


def test_hello_howdy(iobuf: StringIO, fn_hello: Callable) -> None:
    argv = ["John", "-H"]
    args = ["John"]
    kwargs = dict(howdy=True)

    cli, manual = run_cli_and_manual(iobuf, fn_hello, argv, args, kwargs)

    assert cli.startswith("Howdy")
    assert cli == manual


def test_hello_surname(iobuf: StringIO, fn_hello: Callable) -> None:
    argv = ["John", "--lastname", "Doe"]
    args = ["John"]
    kwargs = dict(lastname="Doe")

    cli, manual = run_cli_and_manual(iobuf, fn_hello, argv, args, kwargs)

    assert cli == manual


def test_hello_help(iobuf: StringIO, fn_hello: Callable) -> None:
    argv = ["-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.startswith(f"usage: {test_hello_help.__name__} [-h] [-H] [-l SURNAME] name [age]")
    assert "says hello to you" in cli
    assert "your age (type: int, default: 30)" in cli
    assert "  -H, --hwdy              say howdy instead of hello (type: bool, default: False)" in cli
    assert "  -l, --lastname SURNAME  your SURNAME (type: str, default: None)" in cli


########################################################################################################################
# others


def test_error(iobuf: StringIO) -> None:
    @arguably.command
    def foo():
        pass

    @arguably.command
    def bar():
        arguably.error("!!!")

    argv = ["bar"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert f"{test_error.__name__} bar: error: !!!\n" in cli


def test_version(iobuf: StringIO) -> None:
    import __main__

    __main__.__version__ = "1.2.3"

    @arguably.command
    def foo():
        pass

    argv = ["--version"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, version_flag=True)
    cli = get_and_clear_io(iobuf)

    assert f"{test_version.__name__} 1.2.3\n" == cli


def test_version_flags(iobuf: StringIO) -> None:
    import __main__

    __main__.__version__ = "1.2.3"

    @arguably.command
    def foo():
        pass

    argv = ["-V"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, version_flag=("-V", "--ver"))
    cli = get_and_clear_io(iobuf)

    assert f"{test_version_flags.__name__} 1.2.3\n" == cli


def test_option_flag(iobuf: StringIO) -> None:
    @arguably.command
    def foo(*, bar_: str = "bar"):
        """
        foo
        Args:
            bar_: [-b] bar desc
        """

    argv = ["-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.startswith(f"usage: {test_option_flag.__name__} [-h] [-b BAR]")
    assert "  -b, --bar BAR  bar desc (type: str, default: bar)" in cli


def test_option_flag_rename(iobuf: StringIO) -> None:
    @arguably.command
    def foo(*, bar_: str = "bar"):
        """
        foo
        Args:
            bar_: [-b/--bat] bar desc
        """

    argv = ["-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.startswith(f"usage: {test_option_flag_rename.__name__} [-h] [-b BAT]")
    assert "  -b, --bat BAT  bar desc (type: str, default: bar)" in cli


def test_option_flag_rename_reversed(iobuf: StringIO) -> None:
    @arguably.command
    def foo(*, bar_: str = "bar"):
        """
        foo
        Args:
            bar_: [--bat/-b] bar desc
        """

    argv = ["-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.startswith(f"usage: {test_option_flag_rename_reversed.__name__} [-h] [-b BAT]")
    assert "  -b, --bat BAT  bar desc (type: str, default: bar)" in cli


def test_option_flag_short_only(iobuf: StringIO) -> None:
    @arguably.command
    def foo(*, bar_: str = "bar"):
        """
        foo
        Args:
            bar_: [-b/] bar desc
        """

    argv = ["-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.startswith(f"usage: {test_option_flag_short_only.__name__} [-h] [-b BAR]")
    assert "  -b BAR      bar desc (type: str, default: bar)" in cli


########################################################################################################################
# async_hello()


def test_async_func(iobuf: StringIO, fn_async_hello: Callable) -> None:
    argv = ["John", "-H"]
    args = ["John"]
    kwargs = dict(howdy=True)

    cli, manual = run_cli_and_manual(iobuf, fn_async_hello, argv, args, kwargs, is_async=True)

    assert cli.startswith("Howdy")
    assert cli == manual


if __name__ == "__main__":
    pytest.cmdline.main(["-s", "--verbose", __file__])
