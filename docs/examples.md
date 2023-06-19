# Example Scripts

In the spirit of "show, don't tell", here are a few example scripts. Some of the scripts may be broken up to better show
the code for a subcommand next to its output.

## Hello, world!

A "Hello, world!" script. Can accept a different name to greet, and has a `--shout` option. Because there is only one
command, it's automatically selected - no need to specify subcommand.

The `*`, if you're not familiar, works similarly to `*args` - it separates positional args from keyword-only args. In
`arguably`, keyword-only args each appear as an `--option`.

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/example-hello.py">[source]</a>
</sub></div>

```python
import arguably

@arguably.command
def hello(name="world", *, shout=False):
    """
    says hello to someone
    Args:
        name: {who} to greet
        shout: will only use uppercase
    """
    message = f"Hello, {name}!"
    if shout:
        message = message.upper()
    print(message)

if __name__ == "__main__":
    arguably.run()
```
```console
user@machine:~$ python3 example-hello.py -h
usage: example-hello.py [-h] [--shout] [WHO]

says hello to someone

positional arguments:
  WHO         who to greet (type: str, default: world)

options:
  -h, --help  show this help message and exit
  --shout     will only use uppercase (type: bool, default: False)
```
```console
user@machine:~$ python3 example-hello.py
Hello, world!
```
```console
user@machine:~$ python3 example-hello.py Python
Hello, Python!
```
```console
user@machine:~$ python3 example-hello.py --shout Python
HELLO, PYTHON!
```

## Subcommands

A simple script showing subcommands and multi-level subcommands being used. Outputs for each command are shown next to
the its code.

### Imports and `hey_there`

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/simple.py">[source]</a>
</sub></div>

```python
#!/usr/bin/env python3
"""this docstring is the description for the script"""

import arguably
import builtins

@arguably.command
def hey_there(first_name, last_name: str | None = None):
    """
    this will say hello to someone

    arguments without annotations (`first_name`) default to `str`
        ... unless the type can be inferred from their default value
    any union with `None` is removed, so `last_name` is parsed as `str`

    Args:
        first_name: the {first} name of the person to greet
        last_name: their {last} name
    """
    if last_name is None:
        full_name = first_name
    else:
        full_name = f"{first_name} {last_name}"
    print(f"Hello, {full_name}!")
```
```console
user@machine:~$ python3 simple.py hey-there -h
usage: simple.py hey-there [-h] FIRST [LAST]

this will say hello to someone

positional arguments:
  FIRST       the first name of the person to greet (type: str)
  LAST        their last name (type: str, default: None)

options:
  -h, --help  show this help message and exit
```
```console
user@machine:~$ python3 simple.py hey-there Monty
Hello, Monty!
```
```console
user@machine:~$ python3 simple.py hey-there Monty Python
Hello, Monty Python!
```

### `good`

`good` has two subcommands. The `-s/--shout` option is able to be passed to `good` any time one of these subcommands is
invoked.

```python
@arguably.command(alias="g")
def good(*, shout=False):
    """
    this is a command with two subcommands

    everything after the `*` appears as an `--option`
    `shout` is inferred to be a `bool` because of its default value
        `bool` `--option`s take no value by design

    Args:
        shout: [-s] will shout out the greeting
    """
    if shout:
        # All prints are now UPPERCASE
        global print
        print = lambda msg: builtins.print(msg.upper())
```
```console
user@machine:~$ python3 simple.py good -h
usage: simple.py good [-h] [-s] command ...

this is a command with two subcommands

positional arguments:
  command
    morning    Greet someone early in the day
    night      Say goodbye at night

options:
  -h, --help   show this help message and exit
  -s, --shout  will shout out the greeting (type: bool, default: False)
```

### `good__morning`

```python
@arguably.command
def good__morning(name):
    """Greet someone early in the day"""
    print(f"Good morning, {name}!")
```
```console
user@machine:~$ python3 simple.py good -s morning Monty
GOOD MORNING, MONTY!
```

### `good__night`

```python
@arguably.command
def good__night(name):
    """Say goodbye at night"""
    print(f"Good night, {name}!")
```
```console
user@machine:~$ python3 simple.py good night Python
Good night, Python!
```

### `arguably.run()`

```python
if __name__ == "__main__":
    arguably.run()
```
```console
user@machine:~$ python3 simple.py
usage: simple.py [-h] command ...

this docstring is the description for the script

positional arguments:
  command
    hey-there  this will say hello to someone
    good (g)   this is a command with two subcommands

options:
  -h, --help   show this help message and exit
```

## One of everything

This script includes one of every feature. `arguably` is designed so that you don't have to reach for the tools hidden
behind `Annotated[]` except in special cases, but this script makes heavy use of them.

It's a long script, so it's periodically broken up to show the results on the CLI.

### Imports and `__root__`

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/everything.py">[source]</a>
</sub></div>

```python
#!/usr/bin/env python3
"""
A demo script to show all features
"""

import enum
import operator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import arguably

# used if version_flag is set
__version__ = "1.0.0"

@arguably.command
def __root__(*, verbose: Annotated[int, arguably.arg.count()] = 0):
    """
    __root__ is always called first, before any subcommand.
    It's also run if no subcommand is specified.

    Args:
        verbose: [-v] the verbosity - flag occurrences are counted
    """
    print(f"Verbosity: {verbose}")
    if not arguably.is_target():
        return
    print("__root__ is the target!")
```

```console
user@machine:~$ ./everything.py -vvvv
Verbosity: 4
__root__ is the target!
```

### `add`

```python
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
        *values: scalar {value}s to add to the coords, requires one or more
        include_z: [-z] whether to include a value for Z
    """
    print(f"Coordinates: {coords}")
    if include_z:
        x, y = coords
        z = 0
        coords = (x, y, z)
    for value in values:
        value_arr = (value,) * len(coords)
        coords = tuple(map(operator.add, coords, value_arr))
        print(f"Added {value}: {coords}")
    print(f"Result: {coords}")
```
```console
user@machine:~$ ./everything.py add -h
usage: kitchen-sink add [-h] [-z] X,Y VALUE [VALUE ...]

this is the CLI description for this command

positional arguments:
  X,Y              some coordinates X,Y (type: (int,int))
  VALUE            scalar values to add to the coords, requires one or more (type: int)

options:
  -h, --help       show this help message and exit
  -z, --include-z  whether to include a value for Z (type: bool, default: False)
```
```console
user@machine:~$ ./everything.py add -z 5,5 1 2 3 4
Verbosity: 0
Coordinates: (5, 5)
Added 1: (6, 6, 1)
Added 2: (8, 8, 3)
Added 3: (11, 11, 6)
Added 4: (15, 15, 10)
Result: (15, 15, 10)
```

### `chmod`

```python
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
```
```console
user@machine:~$ ./everything.py chmod -h
usage: kitchen-sink chmod [-h] [-r] [-w] [-x] file

flags break down into multiple --options, one for each flag member.

positional arguments:
  file           the file to modify (type: Path)

options:
  -h, --help     show this help message and exit
  -r, --read     allows for reads
  -w, --write    allows for writes
  -x, --execute  allows for execution
```
```console
user@machine:~$ ./everything.py chmod foo.exe -rwx
Verbosity: 0
file=PosixPath('foo.exe') flags=<Permissions.READ|WRITE|EXECUTE: 7>
```

### `move`

```python
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
```
```console
user@machine:~$ ./everything.py move -h
usage: kitchen-sink move [-h] {up,down,left,right}

enum values are entered by the enum value name

positional arguments:
  {up,down,left,right}  the direction to move (type: Direction)

options:
  -h, --help            show this help message and exit
```
```console
user@machine:~$ ./everything.py move up
Verbosity: 0
Will move 0, 1
```

### `make`

```python
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
```
```console
user@machine:~$ ./everything.py make -h
usage: kitchen-sink make [-h] [--log [LOG]] {build,install,clean}

arguably.arg.choices restricts input values

positional arguments:
  {build,install,clean}  the command to send to `make` (type: str)

options:
  -h, --help             show this help message and exit
  --log [LOG]            the path to log, if any (type: Path, default: None)
```
```console
user@machine:~$ ./everything.py make build
Verbosity: 0
Running `make build`
Will not log
```
```console
user@machine:~$ ./everything.py make build --log
Verbosity: 0
Running `make build`
Logging to ~/.log.txt
```
```console
user@machine:~$ ./everything.py make build --log foo.log
Verbosity: 0
Running `make build`
Logging to foo.log
```

### `arg`

```python
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
```
```console
user@machine:~$ ./everything.py arg -h
usage: kitchen-sink arg [-h] command ...

this has two subcommands. a double underscore __ is used when a space would appear

positional arguments:
  command
    handler   runs a custom handler for input
    builder   builds a complex class - can pick between subtypes of class

options:
  -h, --help  show this help message and exit
```
```console
user@machine:~$ ./everything.py arg
Verbosity: 0
Hello from arg()!
arg() is the target!
```

### `arg__handler`

```python
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
```
```console
user@machine:~$ ./everything.py arg handler -h
usage: kitchen-sink arg handler [-h] version

runs a custom handler for input

positional arguments:
  version     Python version, like 3.11 (type: str)

options:
  -h, --help  show this help message and exit
```
```console
user@machine:~$ ./everything.py arg handler Python-3.10
Verbosity: 0
Hello from arg()!
Python version: 3.10
```

### `arg__builder`

```python
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
        nic: network interfaces - will build subclasses of `Nic`
    """
    print(f"Built nics: {nic}")
```
```console
user@machine:~$ ./everything.py arg builder -h
usage: kitchen-sink arg builder [-h] --nic NIC

builds a complex class - can pick between subtypes of class

options:
  -h, --help  show this help message and exit
  --nic NIC   network interfaces - will build subclasses of `Nic` (type: list[Nic])
```
```console
user@machine:~$ ./everything.py -vvv arg builder --nic tap,model=e1000 --nic user,hostfwd=tcp::10022-:22
Verbosity: 3
Hello from arg()!
Built nics: [TapNic(model='e1000'), UserNic(hostfwd='tcp::10022-:22')]
```

### `list_`

```python
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
```
```console
user@machine:~$ ./everything.py list -h
usage: kitchen-sink list [-h] --output OUTPUT files

lists are supported and use a comma to separate inputs

positional arguments:
  files            input files (type: list[Path])

options:
  -h, --help       show this help message and exit
  --output OUTPUT  outputs (type: list[str])
```
```console
user@machine:~$ ./everything.py list foo.txt,bar.bat --output wifi0,en0 --output en1
Verbosity: 0
Resolved path: .../arguably/etc/scripts/foo.txt
Resolved path: .../arguably/etc/scripts/bar.bat
Will output to wifi0
Will output to en0
Will output to en1
```

### `arguably.run()`

```python
if __name__ == "__main__":
    arguably.run(name="kitchen-sink", version_flag=True)
```
```console
user@machine:~$ ./everything.py -h
usage: kitchen-sink [-h] [--version] [-v] command ...

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
  -v, --verbose  the verbosity - flag occurrences are counted (type: int, default: 0)
```
```console
user@machine:~$ ./everything.py --version
kitchen-sink 1.0.0
```
