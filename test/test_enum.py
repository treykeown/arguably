import sys
from io import StringIO
from typing import Callable, Union

import pytest

import arguably
from . import get_and_clear_io, run_cli_and_manual, Permissions, PermissionsAlt, HiBye


########################################################################################################################
# chmod test cases


def _chmod_no_args(iobuf: StringIO) -> None:
    argv = []

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.endswith("error: the following arguments are required: file\n")


def _chmod_no_rwx(iobuf: StringIO, chmod_impl: Callable) -> None:
    argv = ["script.sh"]
    args = ["script.sh"]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, chmod_impl, argv, args, kwargs)

    assert "script.sh: \n" == cli
    assert cli == manual


def _chmod_all_rwx(iobuf: StringIO, chmod_impl: Callable, permissions: Union[Permissions, PermissionsAlt]) -> None:
    argv = ["script.sh", "-rwx"]
    args = ["script.sh"]
    kwargs = dict(flags=(permissions.READ | permissions.WRITE | permissions.EXECUTE))

    cli, manual = run_cli_and_manual(iobuf, chmod_impl, argv, args, kwargs)

    assert "script.sh: rwx\n" == cli
    assert cli == manual


def _chmod_help(iobuf: StringIO, test_name: str) -> None:
    argv = ["-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert f"usage: {test_name} [-h] [-r] [-w] [-x] file" in cli
    assert "  -r, --read     allows for reads\n" in cli
    assert "  -w, --write    allows for writes\n" in cli
    assert "  -x, --execute  allows for execution\n" in cli


########################################################################################################################
# chmod_alt()


def test_chmod_alt_help(iobuf: StringIO, fn_chmod_alt: Callable) -> None:
    _chmod_help(iobuf, test_chmod_alt_help.__name__)


def test_chmod_alt_no_args(iobuf: StringIO, fn_chmod_alt: Callable) -> None:
    _chmod_no_args(iobuf)


def test_chmod_alt_no_rwx(iobuf: StringIO, fn_chmod_alt: Callable) -> None:
    _chmod_no_rwx(iobuf, fn_chmod_alt)


def test_chmod_alt_all_rwx(iobuf: StringIO, fn_chmod_alt: Callable) -> None:
    _chmod_all_rwx(iobuf, fn_chmod_alt, PermissionsAlt)


########################################################################################################################
# chmod()


def test_chmod_help(iobuf: StringIO, fn_chmod: Callable) -> None:
    _chmod_help(iobuf, test_chmod_help.__name__)


def test_chmod_no_args(iobuf: StringIO, fn_chmod: Callable) -> None:
    _chmod_no_args(iobuf)


def test_chmod_no_rwx(iobuf: StringIO, fn_chmod: Callable) -> None:
    _chmod_no_rwx(iobuf, fn_chmod)


def test_chmod_all_rwx(iobuf: StringIO, fn_chmod: Callable) -> None:
    _chmod_all_rwx(iobuf, fn_chmod, Permissions)


########################################################################################################################
# say()


def test_say_help(iobuf: StringIO, fn_say: Callable) -> None:
    argv = ["-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf)
    cli = get_and_clear_io(iobuf)

    assert cli.startswith(f"usage: {test_say_help.__name__} [-h] {{hi,bye}}")
    assert "  {hi,bye}    which to say" in cli


def test_say_hi(iobuf: StringIO, fn_say: Callable) -> None:
    argv = ["hi"]
    args = [HiBye.HI]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, fn_say, argv, args, kwargs)

    assert cli == HiBye.HI.value
    assert cli == manual


def test_say_annotated_enum_hi(iobuf: StringIO, fn_say_annotated_enum: Callable) -> None:
    argv = ["hi"]
    args = [HiBye.HI]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, fn_say_annotated_enum, argv, args, kwargs)

    assert cli == "which: Hi!\n"
    assert cli == manual


if __name__ == "__main__":
    pytest.cmdline.main(["-s", "--verbose", __file__])
