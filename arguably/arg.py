"""
A collection of methods for adding a modifier to a parameter. Should be used in `Annotated[]`.

Examples:
    ```python
    def foo(
        *,
        verbose: Annotated[int, arguably.arg.count()],
    ):
    ```
"""

import enum
from typing import Union, Callable, Any

import arguably._modifiers as mods


def required() -> mods.RequiredModifier:
    """
    Marks a field as required. For `*args` or a `list[]`, requires at least one item.

    Returns:
        A value for use with `Annotated[]`, stating that this parameter is required.

    Examples:
        ```python
        import arguably
        from typing import Annotated

        @arguably.command
        def email(
            from_: str,
            *to: Annotated[str, arguably.arg.required()]
        ):
            print(f"{from_=}", f"{to=}")

        if __name__ == "__main__":
            arguably.run()
        ```

        ```console
        user@machine:~$ python3 arg-required.py -h
        usage: arg-required.py [-h] from to [to ...]

        positional arguments:
          from        (type: str)
          to          (type: str)

        options:
          -h, --help  show this help message and exit
        ```
        ```console
        user@machine:~$ python3 arg-required.py sender@example.com
        usage: arg-required.py [-h] from to [to ...]
        arg-required.py: error: the following arguments are required: to
        ```
    """
    return mods.RequiredModifier()


def count() -> mods.CountedModifier:
    """
    Counts the number of times a flag is given. For example, `-vvvv` would yield `4`.

    Returns:
        A value for use with `Annotated[]`, stating that this parameter should be counted.

    Examples:
        ```python
        import arguably
        from typing import Annotated

        @arguably.command
        def process(
            *,
            verbose: Annotated[int, arguably.arg.count()],
        ):
            \"\"\"
            :param verbose: [-v] verbosity
            \"\"\"
            print(f"{verbose=}")

        if __name__ == "__main__":
            arguably.run()
        ```

        ```console
        user@machine:~$ python3 arg-count.py -vvvv
        verbose=4
        ```
    """
    return mods.CountedModifier()


def choices(*choices: Union[str, enum.Enum]) -> mods.ChoicesModifier:
    """
    Specifies a fixed set of values that a parameter is allowed to be. If a parameter is an `enum.Enum` type, this
    logic is already used to restrict the inputs to be one of the enum entries.

    Args:
        *choices: The allowed values. Must all be of the same type, and be compatible with the annotated type for
            this parameter.

    Returns:
        A value for use with `Annotated[]`, stating that this parameter has a fixed set of choices.

    Examples:
        ```python
        import arguably
        from typing import Annotated

        @arguably.command
        def move(
            direction: Annotated[str, arguably.arg.choices("left", "right", "up", "down")]
        ):
            \"\"\"An enum is usually recommended for cases like this'''
            print(f"{direction=}")

        if __name__ == "__main__":
            arguably.run()
        ```

        ```console
        user@machine:~$ python3 arg-choices.py north
        usage: arg-choices.py [-h] {left,right,up,down}
        arg-choices.py: error: argument direction: invalid choice: 'north' (choose from 'left', 'right', 'up', 'down')
        ```
    """
    return mods.ChoicesModifier(choices)


def missing(omit_value: str) -> mods.MissingArgDefaultModifier:
    """
    Allows an option to be specified, but its value be omitted. In the case where the value is given, the value is
    used, but if it is omitted, `omit_value` will be used.

    Args:
        omit_value: The value that will be used if the flag is present, but the value is omitted.

    Returns:
        A value for use with `Annotated[]`, stating that this parameter has a special value if the flag is present,
            but no value is provided.

    Examples:
        ```python
        import arguably
        from pathlib import Path
        from typing import Annotated

        @arguably.command
        def do_something(
            *,
            log: Annotated[Path | None, arguably.arg.missing("~/.log.txt")] = None
        ):
            print(f"{log=}")

        if __name__ == "__main__":
            arguably.run()
        ```

        ```console
        user@machine:~$ python3 arg-missing.py
        log=None
        user@machine:~$ python3 arg-missing.py --log
        log=PosixPath('~/.log.txt')
        user@machine:~$ python3 arg-missing.py --log foo.log
        log=PosixPath('foo.log')
        ```
    """
    return mods.MissingArgDefaultModifier(omit_value)


def handler(func: Callable[[str], Any]) -> mods.HandlerModifier:
    """
    Causes a user-provided handler to be used to process the input string, instead of trying to process it using
    the types from type annotations.

    Args:
        func: The function to call to process the input string.

    Returns:
        A value for use with `Annotated[]`, stating that this parameter has a specific handler to call.

    Examples:
        ```python
        import arguably
        from typing import Annotated

        @arguably.command
        def handle_it(
            version: Annotated[int, arguably.arg.handler(lambda s: int(s.split("-")[-1]))] = None
        ):
            print(f"{version=}")

        if __name__ == "__main__":
            arguably.run()
        ```

        ```console
        user@machine:~$ python3 arg-handler.py Python-3
        version=3
        ```
    """
    return mods.HandlerModifier(func)


def builder() -> mods.BuilderModifier:
    """
    Causes the arguably builder logic to be used instead of trying to instantiate the type from the input string.

    Returns:
        A value for use with `Annotated[]`, stating that this parameter should use the builder logic.

    Examples:
        ```python
        import arguably
        from dataclasses import dataclass
        from typing import Annotated

        class Nic: ...

        @arguably.subtype(alias="tap")
        @dataclass
        class TapNic(Nic):
            model: str

        @arguably.subtype(alias="user")
        @dataclass
        class UserNic(Nic):
            hostfwd: str

        @arguably.command
        def qemu_style(*, nic: Annotated[list[Nic], arguably.arg.builder()]):
            print(f"{nic=}")

        if __name__ == "__main__":
            arguably.run()
        ```

        ```console
        user@machine:~$ ./readme-2.py --nic tap,model=e1000 --nic user,hostfwd=tcp::10022-:22
        nic=[TapNic(model='e1000'), UserNic(hostfwd='tcp::10022-:22')]
        ```
    """
    return mods.BuilderModifier()
