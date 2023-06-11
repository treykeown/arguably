def test(name: str, age: int) -> None:
    """
    just a test
    :param name: the name
    :param age: the age
    """
    print(f"name: {name}, age+1: {age + 1}")


class Foo:
    def __init__(self, bar: int):
        """
        foo!
        :param bar: bar!
        """
        print(f"{type(self).__name__} initialized with {bar}")

    @staticmethod
    def sm(name: str) -> None:
        """
        staticmethod test func
        :param name: the name
        """
        print(f"{name}")

    @classmethod
    def cm(cls, name: str = "testname") -> None:
        """classmethod test func"""
        print(f"{cls.__name__}, {name}")

    def normal(self, foo: int) -> None:
        """a normal method, should not appear"""
        print(f"{self}, foo+1: {foo+1}")
