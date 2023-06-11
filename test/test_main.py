import runpy

import pytest

from . import append_argv, run_cli_and_manual_main


def test_no_args(capsys: pytest.CaptureFixture):
    with pytest.raises(SystemExit):
        runpy.run_module("arguably", run_name="__main__")
    out, err = capsys.readouterr()

    assert out == ""
    assert (
        err == "usage: arguably [-h] [--debug] file [args ...]\n"
        "arguably: error: the following arguments are required: file\n"
    )


def test_target1_help(capsys: pytest.CaptureFixture):
    with append_argv("test/assets/target1.py"):
        runpy.run_module("arguably", run_name="__main__")
    out, err = capsys.readouterr()

    assert out.startswith("usage: target1 [-h] command ...")
    assert " test " in out
    assert " foo " in out
    assert " foo.sm " in out
    assert " foo.cm " in out
    assert " foo.normal " not in out
    assert err == ""


def test_target1_test(capsys: pytest.CaptureFixture):
    from .assets.target1 import test

    argv = ["test", "john", "50"]
    args = ["john", 50]
    kwargs = dict()

    cli, manual = run_cli_and_manual_main(capsys, "test/assets/target1.py", test, argv, args, kwargs)

    assert cli == manual


def test_target1_foo(capsys: pytest.CaptureFixture):
    from .assets.target1 import Foo

    argv = ["foo", "50"]
    args = [50]
    kwargs = dict()

    cli, manual = run_cli_and_manual_main(capsys, "test/assets/target1.py", Foo, argv, args, kwargs)

    assert cli == manual


def test_target1_foo_sm(capsys: pytest.CaptureFixture):
    from .assets.target1 import Foo

    argv = ["foo.sm", "hello"]
    args = ["hello"]
    kwargs = dict()

    cli, manual = run_cli_and_manual_main(capsys, "test/assets/target1.py", Foo.sm, argv, args, kwargs)

    assert cli == manual


def test_target1_foo_cm(capsys: pytest.CaptureFixture):
    from .assets.target1 import Foo

    argv = ["foo.cm"]
    args = []
    kwargs = dict()

    cli, manual = run_cli_and_manual_main(capsys, "test/assets/target1.py", Foo.cm, argv, args, kwargs)

    assert cli == manual


def test_target2_tuple_method(capsys: pytest.CaptureFixture):
    from .assets.target2 import tuple_method

    argv = ["tuple-method", "abc,2,3.14"]
    args = [("abc", 2, 3.14)]
    kwargs = dict()

    cli, manual = run_cli_and_manual_main(capsys, "test/assets/target2.py", tuple_method, argv, args, kwargs)

    assert cli == manual


if __name__ == "__main__":
    pytest.cmdline.main(["-s", "--verbose", __file__])
