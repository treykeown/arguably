#!/usr/bin/env python3
"""
A demo script to show all features
"""

import enum
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import arguably

# used if version_flag is set
__version__ = "1.0.0"


@arguably.command
def add(
    coords: tuple[int, int],
    *values: Annotated[int, arguably.arg.required()],
    include_z: bool = False,
):
    """
    this is the CLI description for this command
    Args:
        coords: some coordinates {X,Y}
        *values: scalar {value}s to add to the coords
        include_z: [-z] whether to include a value for Z
    """
    print(f"Coordinates: {coords}")
    x, y = coords
    z = 0
    for value in values:
        print(f"Adding {value}")
        x += value
        y += value
        z += value
    if include_z:
        print(f"Result: {(x, y, z)}")
    else:
        print(f"Result: {(x, y)}")


class Permissions(enum.Flag):
    READ = 4
    """[-r] allows for reads"""
    WRITE = 2
    """[-w] allows for writes"""
    EXECUTE = 1
    """[-x] allows for execution"""

@arguably.command
def chmod(file: Path, *, flags: Permissions = Permissions(0)):
    """
    flags break down into multiple --options, one for each flag member.
    the docstring for each flag member is used.
    Args:
        file: the file to modify
        flags: permission flags
    """
    print(f"{file=}", f"{flags=}")


class Direction(enum.Enum):
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

@arguably.command
def move(direction: Direction):
    """
    enum values are entered by the enum value name
    Args:
        direction: the direction to move
    """
    dx, dy = direction.value
    print(f"Will move {dx}, {dy}")


@arguably.command
def make(
    target: Annotated[str, arguably.arg.choices("build", "install", "clean")],
    *,
    log: Annotated[Path | None, arguably.arg.missing("~/.log.txt")] = None,
):
    """
    arguably.arg.choices restricts input values
    arguably.arg.missing provides a value if the flag is specified but value omitted
    Args:
        target: the command to send to `make`
        log: the path to log, if any
    """
    print(f"Running `make {target}`")
    if log is None:
        print("Will not log")
    else:
        print(f"Logging to {log}")


@arguably.command
def arg():
    """
    this has two subcommands. a double underscore __ is used when a space would appear
      * arg__handler -> "arg handler"
      * arg__builder -> "arg builder"
    """
    print("Hello from arg()!")
    if arguably.is_target():
        print("arg() is the target!")


@arguably.command
def arg__handler(
    version: Annotated[str, arguably.arg.handler(lambda s: s.removeprefix("Python-"))]
):
    """
    runs a custom handler for input
    arguably.arg.handler allows for arbitrary functions to handle inputs
    this one removes a prefix of "Python-" before passing the value along
    Args:
        version: Python version, like 3.11
    """
    print(f"Python version: {version}")


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
def arg__builder(
    *,
    nic: Annotated[list[Nic], arguably.arg.builder()]
):
    """
    builds a complex class - can pick between subtypes of class
    Args:
        nic:
    """
    print(f"Built nics: {nic}")


@arguably.command
def list_(files: list[Path], *, output: list[str]):
    """
    lists are supported and use a comma to separate inputs
    an empty list is a single dash `-`
    if a list appears as an `--option`, it can be repeated
    Args:
        files: input files
        output: outputs
    """
    for file in files:
        print(f"Resolved path: {file.resolve()}")
    for out in output:
        print(f"Will output to {out}")


@arguably.command
def __root__(*, verbose: Annotated[int, arguably.arg.count()] = 0):
    """
    __root__ is always called first, before any subcommand
    Args:
        verbose: [-v] the verbosity
    """
    print(f"Verbosity: {verbose}")
    if not arguably.is_target():
        return
    print("__root__ is the target!")


if __name__ == "__main__":
    arguably.run(name="EVERYthing", version_flag=True)
