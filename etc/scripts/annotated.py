from pathlib import Path

import arguably
from dataclasses import dataclass
from typing import Annotated

@arguably.command
def email(
    from_: str,
    *to: Annotated[str, arguably.arg.required()]
):
    print(f"{from_=}", f"{to=}")

@arguably.command
def process(
    *,
    verbose: Annotated[int, arguably.arg.count()],
):
    """
    :param verbose: [-v] verbosity
    """
    print(f"{verbose=}")

@arguably.command
def move(
    direction: Annotated[str, arguably.arg.choices("left", "right", "up", "down")]
):
    """An enum is usually recommended for cases like this"""
    print(f"{direction=}")

@arguably.command
def do_something(
    *,
    log: Annotated[Path | None, arguably.arg.missing("~/.log.txt")] = None
):
    print(f"{log=}")

@arguably.command
def handle_it(
    version: Annotated[int, arguably.arg.handler(lambda s: int(s.split("-")[-1]))] = None
):
    print(f"{version=}")

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
def builder(
    *,
    nic: Annotated[list[Nic], arguably.arg.builder()]
):
    print(f"{nic=}")

if __name__ == "__main__":
    arguably.run()
