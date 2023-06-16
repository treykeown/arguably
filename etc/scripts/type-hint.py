import arguably
from pathlib import Path

@arguably.command
def basic(name: str, age: int, percent: float):
    """all basic types like str, int, float, etc are supported"""
    print(f"{name=}", f"{age=}", f"{percent=}")

@arguably.command
def tuple_(value: tuple[str, int, float]):
    """tuples can contain any supported type that isn't a list or tuple"""
    print(f"{value=}")

class UserType:
    def __init__(self, val: str):
        self.val = int(val)
    def __repr__(self):
        return f"{type(self).__name__}(val={self.val})"

@arguably.command
def any_type(value: UserType, path: Path):
    """any type that can be initialized from a string is supported"""
    print(f"{value=}", f"{path=}")

@arguably.command
def list_(files: list[Path], *, nums: list[int]):
    """lists are supported. if they appear as an option
    (like `coord` does), they can be specified multiple times"""
    print(f"{files=}", f"{nums=}")

if __name__ == "__main__":
    arguably.run()
