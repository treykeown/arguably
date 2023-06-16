# target this with `python3 -m arguably party-trick.py`

def hello() -> None:
    """this is the docstring for a function in the script"""

def goodbye() -> None:
    """any function from a script can be called"""

class A_Class:
    def __init__(self):
        """so can any __init__ for objects defined in the script"""

    @staticmethod
    def func_static():
        """a @staticmethod on a class can be called"""

    @classmethod
    def func_cls(cls):
        """so can a @classmethod"""

    def normal(self) -> None:
        """but normal methods can't"""
