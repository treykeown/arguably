"""Test cases for list and tuple default values"""
import sys
from io import StringIO

import arguably
from . import get_and_clear_io, run_cli_and_manual


def test_list_with_default(iobuf: StringIO) -> None:
    """Test that list with default value is respected"""
    @arguably.command
    def main(*, samples: list[int] = [2, 3, 5]):
        iobuf.write(f"samples={samples}\n")
    
    argv = []
    args = []
    kwargs = dict(samples=[2, 3, 5])
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "samples=[2, 3, 5]" in cli
    assert cli == manual


def test_tuple_with_default(iobuf: StringIO) -> None:
    """Test that tuple with default value is respected"""
    @arguably.command
    def main(*, samples: tuple[int, ...] = (2, 3)):
        iobuf.write(f"samples={samples}\n")
    
    argv = []
    args = []
    kwargs = dict(samples=(2, 3))
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "samples=(2, 3)" in cli
    assert cli == manual


def test_fixed_tuple_with_default(iobuf: StringIO) -> None:
    """Test that fixed-size tuple with default value is respected"""
    @arguably.command
    def main(*, coords: tuple[int, int] = (10, 20)):
        iobuf.write(f"coords={coords}\n")
    
    argv = []
    args = []
    kwargs = dict(coords=(10, 20))
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "coords=(10, 20)" in cli
    assert cli == manual


def test_list_with_default_overridden(iobuf: StringIO) -> None:
    """Test that list with default value can be overridden"""
    @arguably.command
    def main(*, samples: list[int] = [2, 3, 5]):
        iobuf.write(f"samples={samples}\n")
    
    argv = ["--samples", "7,11"]
    args = []
    kwargs = dict(samples=[7, 11])
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "samples=[7, 11]" in cli
    assert cli == manual


def test_tuple_with_default_overridden(iobuf: StringIO) -> None:
    """Test that tuple with default value can be overridden"""
    @arguably.command
    def main(*, samples: tuple[int, ...] = (2, 3)):
        iobuf.write(f"samples={samples}\n")
    
    argv = ["--samples", "7,11"]
    args = []
    kwargs = dict(samples=(7, 11))
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "samples=(7, 11)" in cli
    assert cli == manual


def test_list_without_default(iobuf: StringIO) -> None:
    """Test that list without default value uses empty list"""
    @arguably.command
    def main(*, samples: list[int] = []):
        iobuf.write(f"samples={samples}\n")
    
    argv = []
    args = []
    kwargs = dict(samples=[])
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "samples=[]" in cli
    assert cli == manual


def test_tuple_without_default(iobuf: StringIO) -> None:
    """Test that tuple without default value uses empty tuple"""
    @arguably.command
    def main(*, samples: tuple[int, ...] = ()):
        iobuf.write(f"samples={samples}\n")
    
    argv = []
    args = []
    kwargs = dict(samples=())
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "samples=()" in cli
    assert cli == manual


def test_list_positional_with_default(iobuf: StringIO) -> None:
    """Test that positional list with default value is respected"""
    @arguably.command
    def main(samples: list[int] = [2, 3, 5]):
        iobuf.write(f"samples={samples}\n")
    
    argv = []
    args = [[2, 3, 5]]
    kwargs = dict()
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "samples=[2, 3, 5]" in cli
    assert cli == manual


def test_tuple_positional_with_default(iobuf: StringIO) -> None:
    """Test that positional tuple with default value is respected"""
    @arguably.command
    def main(samples: tuple[int, ...] = (2, 3)):
        iobuf.write(f"samples={samples}\n")
    
    argv = []
    args = [(2, 3)]
    kwargs = dict()
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "samples=(2, 3)" in cli
    assert cli == manual


def test_optional_tuple_with_none_default(iobuf: StringIO) -> None:
    """Test that Optional[tuple] with None default preserves None"""
    @arguably.command
    def main(*, warmup_steps: tuple[int, ...] | None = None):
        iobuf.write(f"warmup_steps={warmup_steps}\n")
    
    argv = []
    args = []
    kwargs = dict(warmup_steps=None)
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "warmup_steps=None" in cli
    assert cli == manual


def test_optional_list_with_none_default(iobuf: StringIO) -> None:
    """Test that Optional[list] with None default preserves None"""
    @arguably.command
    def main(*, items: list[str] | None = None):
        iobuf.write(f"items={items}\n")
    
    argv = []
    args = []
    kwargs = dict(items=None)
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "items=None" in cli
    assert cli == manual


def test_optional_tuple_with_none_default_overridden(iobuf: StringIO) -> None:
    """Test that Optional[tuple] with None default can be overridden"""
    @arguably.command
    def main(*, warmup_steps: tuple[int, ...] | None = None):
        iobuf.write(f"warmup_steps={warmup_steps}\n")
    
    argv = ["--warmup-steps", "100,200"]
    args = []
    kwargs = dict(warmup_steps=(100, 200))
    
    cli, manual = run_cli_and_manual(iobuf, main, argv, args, kwargs)
    
    assert "warmup_steps=(100, 200)" in cli
    assert cli == manual
