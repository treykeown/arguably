"""this is the docstring for the whole script"""
__version__ = "2.3.4"  # __version__ will be used if present

def hello(name) -> None:
    """
    this is hello's docstring
    Args:
        name: argument docstrings are automatically used
    """
    print(f"Hello, {name}!")

def goodbye(name) -> None:
    """any function from a script can be called"""
    print(f"Goodbye, {name}!")

class SomeClass:
    def __init__(self):
        """so can any __init__ for objects defined in the script"""
        print("__init__")

    @staticmethod
    def func_static(string="Monty"):
        """a @staticmethod on a class can be called"""
        print(f"{string=}")

    @classmethod
    def func_cls(cls, number=1):
        """so can a @classmethod"""
        print(f"{number=}")

    def normal(self) -> None:
        """but normal methods can't"""
        print("instance method")
