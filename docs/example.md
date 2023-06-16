# Example Script

In the spirit of "show, don't tell", here's a script that includes one of everything.

```python
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
```
```console
user@machine:~$ ./everything.py -h
usage: EVERYthing [-h] [--version] [-v] command ...

A demo script to show all features

positional arguments:
  command
    add          this is the CLI description for this command
    chmod        flags break down into multiple --options, one for each flag member.
    move         enum values are entered by the enum value name
    make         arguably.arg.choices restricts input values
    arg          this has two subcommands. a double underscore __ is used when a space would appear
    list         lists are supported and use a comma to separate inputs

options:
  -h, --help     show this help message and exit
  --version      show program's version number and exit
  -v, --verbose  the verbosity (type: int, default: 0)

user@machine:~$ ./everything.py --version
EVERYthing 1.0.0

user@machine:~$ ./everything.py -vvvv
Verbosity: 4
__root__ is the target!

user@machine:~$ ./everything.py add -h
usage: EVERYthing add [-h] [-z] X,Y VALUE [VALUE ...]

this is the CLI description for this command

positional arguments:
  X,Y              some coordinates X,Y (type: (int,int))
  VALUE            scalar values to add to the coords (type: int)

options:
  -h, --help       show this help message and exit
  -z, --include-z  whether to include a value for Z (type: bool, default: False)

user@machine:~$ ./everything.py -vvvv add -z 10,10 1 2 3 4
Verbosity: 4
Coordinates: (10, 10)
Adding 1
Adding 2
Adding 3
Adding 4
Result: (20, 20, 10)

user@machine:~$ ./everything.py chmod -h
usage: EVERYthing chmod [-h] [-r] [-w] [-x] file

flags break down into multiple --options, one for each flag member.

positional arguments:
  file           the file to modify (type: Path)

options:
  -h, --help     show this help message and exit
  -r, --read     allows for reads
  -w, --write    allows for writes
  -x, --execute  allows for execution

user@machine:~$ ./everything.py chmod foo.exe -rwx
Verbosity: 0
file=PosixPath('foo.exe') flags=<Permissions.READ|WRITE|EXECUTE: 7>

user@machine:~$ ./everything.py move -h
usage: EVERYthing move [-h] {up,down,left,right}

enum values are entered by the enum value name

positional arguments:
  {up,down,left,right}  the direction to move (type: Direction)

options:
  -h, --help            show this help message and exit

user@machine:~$ ./everything.py move up
Verbosity: 0
Will move 0, 1

user@machine:~$ ./everything.py make -h
usage: EVERYthing make [-h] [--log [LOG]] {build,install,clean}

arguably.arg.choices restricts input values

positional arguments:
  {build,install,clean}  the command to send to `make` (type: str)

options:
  -h, --help             show this help message and exit
  --log [LOG]            the path to log, if any (type: Path, default: None)

user@machine:~$ ./everything.py make build
Verbosity: 0
Running `make build`
Will not log

user@machine:~$ ./everything.py make build --log
Verbosity: 0
Running `make build`
Logging to ~/.log.txt

user@machine:~$ ./everything.py make build --log foo.log
Verbosity: 0
Running `make build`
Logging to foo.log

user@machine:~$ ./everything.py arg -h
usage: EVERYthing arg [-h] command ...

this has two subcommands. a double underscore __ is used when a space would appear

positional arguments:
  command
    handler   runs a custom handler for input
    builder   builds a complex class - can pick between subtypes of class

options:
  -h, --help  show this help message and exit

user@machine:~$ ./everything.py arg
Verbosity: 0
Hello from arg()!
arg() is the target!

user@machine:~$ ./everything.py arg handler -h
usage: EVERYthing arg handler [-h] version

runs a custom handler for input

positional arguments:
  version     Python version, like 3.11 (type: str)

options:
  -h, --help  show this help message and exit

user@machine:~$ ./everything.py arg handler Python-3.10
Verbosity: 0
Hello from arg()!
Python version: 3.10

user@machine:~$ ./everything.py arg builder -h
usage: EVERYthing arg builder [-h] --nic NIC

builds a complex class - can pick between subtypes of class

options:
  -h, --help  show this help message and exit
  --nic NIC   (type: list[Nic])

user@machine:~$ ./everything.py -vvv arg builder --nic tap,model=e1000 --nic user,hostfwd=tcp::10022-:22
Verbosity: 3
Hello from arg()!
Built nics: [TapNic(model='e1000'), UserNic(hostfwd='tcp::10022-:22')]

user@machine:~$ ./everything.py list -h
usage: EVERYthing list [-h] --output OUTPUT files

lists are supported and use a comma to separate inputs

positional arguments:
  files            input files (type: list[Path])

options:
  -h, --help       show this help message and exit
  --output OUTPUT  outputs (type: list[str])

user@machine:~$ ./everything.py list foo.txt,bar.bat --output wifi0,en0 --output en1
Verbosity: 0
Resolved path: /Users/gosling/Documents/Projects/arguably/etc/scripts/foo.txt
Resolved path: /Users/gosling/Documents/Projects/arguably/etc/scripts/bar.bat
Will output to wifi0
Will output to en0
Will output to en1
```
