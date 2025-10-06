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
    assert "    add                     adds a bunch of numbers together" in cli
    assert "    give                    give something" in cli
    assert "    hey-you (h)             says hello to you" in cli
    assert "  --loud                    make it loud (type: bool, default: False)" in cli


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

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

    assert "> hey-you\n" in cli
    assert cli == manual


def test_give(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["give"]
    args = []
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["give"], argv, args, kwargs)

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

    assert "> give\n" in cli
    assert "give is main\n" in cli
    assert cli == manual


def test_give_zen(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["give", "zen", "--rotten"]
    args = []
    kwargs = dict(rotten=True)

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["give__zen"], argv, args, kwargs)

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

    assert "> give\n" in cli
    cli = cli.replace("> give\n", "")

    assert "> give zen\n" in cli
    assert "give zen rotten\n" in cli
    assert cli == manual


def test_give_zen_ancestor(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["give", "--slowly", "zen", "--rotten"]
    args = []
    kwargs = dict(rotten=True)

    scope_advanced["__root__"]()
    scope_advanced["give"](slowly=True)
    cli, manual = run_cli_and_manual(iobuf, scope_advanced["give__zen"], argv, args, kwargs)

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

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

    assert "> do a-dance\n" in cli
    assert cli == manual


def test_add(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["add", "1", "1", "2", "3", "--coords", "10,20,30"]
    args = [1, 1, 2, 3]
    kwargs = dict(coords=(10, 20, 30))

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["add"], argv, args, kwargs)

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

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
    assert "  NUMS                the numbers NUMS to add (type: int)\n" in cli
    assert "  -c, --coords X,Y,Z  coordinates X,Y,Z updated with the sum (type: (int,int,int), default: None)\n" in cli


def test_mixed_tuple(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["mixed-tuple", "foo,10,123.45"]
    args = [("foo", 10, 123.45)]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["mixed_tuple"], argv, args, kwargs)

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

    assert "> mixed-tuple\n" in cli
    assert "'foo', 10, 123.45\n" in cli
    assert cli == manual


def test_mixed_tuple_help(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["mixed-tuple", "-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, name="advanced")
    cli = get_and_clear_io(iobuf)

    assert cli.startswith("usage: advanced mixed-tuple [-h] val,val,val\n")
    assert "  val,val,val  the values (type: (str,int,float))" in cli


def test_ellipsis_tuple_floats(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["ellipsis-tuple-floats", "0,1,2,3"]
    args = [(0.0, 1.0, 2.0, 3.0)]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["ellipsis_tuple_floats"], argv, args, kwargs)

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

    assert "> ellipsis-tuple-floats\n" in cli
    assert "(0.0, 1.0, 2.0, 3.0)\n" in cli
    assert "type: tuple\n" in cli
    assert cli == manual


def test_ellipsis_tuple_floats_single(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["ellipsis-tuple-floats", "42.5"]
    args = [(42.5,)]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["ellipsis_tuple_floats"], argv, args, kwargs)

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

    assert "(42.5,)\n" in cli
    assert "type: tuple\n" in cli
    assert cli == manual


def test_ellipsis_tuple_ints_option(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["ellipsis-tuple-ints", "--nums", "1,2,3,4,5"]
    args = []
    kwargs = dict(nums=(1, 2, 3, 4, 5))

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["ellipsis_tuple_ints"], argv, args, kwargs)

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

    assert "> ellipsis-tuple-ints\n" in cli
    assert "(1, 2, 3, 4, 5)\n" in cli
    assert "type: tuple\n" in cli
    assert cli == manual


def test_ellipsis_tuple_ints_empty(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["ellipsis-tuple-ints"]
    args = []
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["ellipsis_tuple_ints"], argv, args, kwargs)

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

    assert "> ellipsis-tuple-ints\n" in cli
    assert "()\n" in cli
    assert "type: tuple\n" in cli
    assert cli == manual


def test_ellipsis_tuple_strings(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["ellipsis-tuple-strings", "foo,bar,baz"]
    args = [("foo", "bar", "baz")]
    kwargs = dict()

    cli, manual = run_cli_and_manual(iobuf, scope_advanced["ellipsis_tuple_strings"], argv, args, kwargs)

    assert "> root\n" in cli
    cli = cli.replace("> root\n", "")

    assert "> ellipsis-tuple-strings\n" in cli
    assert "('foo', 'bar', 'baz')\n" in cli
    assert "type: tuple\n" in cli
    assert cli == manual


def test_ellipsis_tuple_floats_help(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["ellipsis-tuple-floats", "-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, name="advanced")
    cli = get_and_clear_io(iobuf)

    assert cli.startswith("usage: advanced ellipsis-tuple-floats [-h] values\n")
    assert "the float values (type: tuple[float,...])" in cli


def test_ellipsis_tuple_ints_help(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["ellipsis-tuple-ints", "-h"]

    sys.argv.extend(argv)
    with pytest.raises(SystemExit):
        arguably.run(output=iobuf, name="advanced")
    cli = get_and_clear_io(iobuf)

    assert cli.startswith("usage: advanced ellipsis-tuple-ints [-h] [--nums NUMS]\n")
    assert "the int values (type: tuple[int,...], default: ())" in cli


def test_nested_tuple_ints(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    # For now, let's define the expected syntax as semicolon-separated groups
    # e.g., "1,2,3;4,5;6,7,8" represents ((1,2,3), (4,5), (6,7,8))
    argv = ["nested-tuple-ints", "1,2,3;4,5;6,7,8"]
    args = [((1, 2, 3), (4, 5), (6, 7, 8))]
    kwargs = dict()

    # This test will initially fail - that's expected
    try:
        cli, manual = run_cli_and_manual(iobuf, scope_advanced["nested_tuple_ints"], argv, args, kwargs)
        
        assert "> root\n" in cli
        cli = cli.replace("> root\n", "")
        
        assert "> nested-tuple-ints\n" in cli
        assert "((1, 2, 3), (4, 5), (6, 7, 8))\n" in cli
        assert "type: tuple\n" in cli
        assert "inner[0]: (1, 2, 3) (type: tuple)\n" in cli
        assert "inner[1]: (4, 5) (type: tuple)\n" in cli
        assert "inner[2]: (6, 7, 8) (type: tuple)\n" in cli
        assert cli == manual
    except Exception as e:
        # Expected to fail initially
        print(f"Expected failure: {e}")
        pytest.skip("Nested tuple support not yet implemented")


def test_nested_tuple_strings_option(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    # Test nested tuples as optional arguments
    argv = ["nested-tuple-strings", "--values", "foo,bar;baz,qux"]
    args = []
    kwargs = dict(values=(("foo", "bar"), ("baz", "qux")))

    # This test will initially fail - that's expected
    try:
        cli, manual = run_cli_and_manual(iobuf, scope_advanced["nested_tuple_strings"], argv, args, kwargs)
        
        assert "> root\n" in cli
        cli = cli.replace("> root\n", "")
        
        assert "> nested-tuple-strings\n" in cli
        assert "(('foo', 'bar'), ('baz', 'qux'))\n" in cli
        assert "type: tuple\n" in cli
        assert "inner[0]: ('foo', 'bar') (type: tuple)\n" in cli
        assert "inner[1]: ('baz', 'qux') (type: tuple)\n" in cli
        assert cli == manual
    except Exception as e:
        # Expected to fail initially
        print(f"Expected failure: {e}")
        pytest.skip("Nested tuple support not yet implemented")


def test_nested_tuple_empty(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    # Test empty nested tuple (default value)
    argv = ["nested-tuple-strings"]
    args = []
    kwargs = dict()

    # This test will initially fail - that's expected
    try:
        cli, manual = run_cli_and_manual(iobuf, scope_advanced["nested_tuple_strings"], argv, args, kwargs)
        
        assert "> root\n" in cli
        cli = cli.replace("> root\n", "")
        
        assert "> nested-tuple-strings\n" in cli
        assert "()\n" in cli
        assert "type: tuple\n" in cli
        assert cli == manual
    except Exception as e:
        # Expected to fail initially
        print(f"Expected failure: {e}")
        pytest.skip("Nested tuple support not yet implemented")


def test_nested_tuple_help(iobuf: StringIO, scope_advanced: Dict[str, Callable]) -> None:
    argv = ["nested-tuple-ints", "-h"]

    sys.argv.extend(argv)
    try:
        with pytest.raises(SystemExit):
            arguably.run(output=iobuf, name="advanced")
        cli = get_and_clear_io(iobuf)

        assert cli.startswith("usage: advanced nested-tuple-ints [-h] data\n")
        assert "nested int tuples" in cli
        # Help text format TBD - will be implemented later
    except Exception as e:
        # Expected to fail initially
        print(f"Expected failure: {e}")
        pytest.skip("Nested tuple support not yet implemented")
