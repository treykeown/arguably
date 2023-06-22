# Type hints

## Introduction

`arguably` uses type hints to convert CLI input from strings to the type needed by your function.

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/type-hint.py">[source]</a>
</sub></div>

```python
import arguably
from pathlib import Path

@arguably.command
def basic(name: str, age: int, percent: float):
    """all basic types like str, int, float, etc are supported"""
    print(f"{name=}", f"{age=}", f"{percent=}")
```
```console
user@machine:~$ python3 type-hint.py basic Monty 42 33.3
name='Monty' age=42 percent=33.3
```
```python
@arguably.command
def tuple_(value: tuple[str, int, float]):
    """tuples can contain any supported type that isn't a list or tuple"""
    print(f"{value=}")
```
```console
user@machine:~$ python3 type-hint.py tuple foo,1,3.14
value=('foo', 1, 3.14)
```
```python
class UserType:
    def __init__(self, val: str):
        self.val = int(val)
    def __repr__(self):
        return f"{type(self).__name__}(val={self.val})"

@arguably.command
def any_type(value: UserType, path: Path):
    """any type that can be initialized from a string is supported"""
    print(f"{value=}", f"{path=}")
```
```console
user@machine:~$ python3 type-hint.py any-type 123 .
value=UserType(val=123) path=PosixPath('.')
```
```python
@arguably.command
def list_(files: list[Path], *, nums: list[int]):
    """lists are supported. if they appear as an option
    (like `coord` does), they can be specified multiple times"""
    print(f"{files=}", f"{nums=}")
```
```console
user@machine:~$ python3 type-hint.py list foo.txt,bar.exe --nums 1 --nums 2,3
files=[PosixPath('foo.txt'), PosixPath('bar.exe')] nums=[1, 2, 3]
```
```python
if __name__ == "__main__":
    arguably.run()
```

## Allowed types

### "Normal" types

Any type that can be constructed by passing in a single string value is allowed. This includes:

* Basic built-in types like `str`, `int`, `float`, `bool`
* Other built-ins like `pathlib.Path`
* Any user-defined classes that also have this kind of constructor

```python
@dataclass
class GoodClass1:
    """Example of a user-defined class that can be used"""
    name: str

@dataclass
class BadClass1:
    """NOT USABLE: This class won't work, since it should take in an integer"""
    age: int

@dataclass
class BadClass2:
    """NOT USABLE: This class won't work, since it takes in multiple arguments"""
    first_name: str
    last_name: str

class GoodClass2:
    """Example of another user-defined class that can be used"""
    def __init__(self, value: str | int):
        if isinstance(value, str):
            value = int(str)
        self._int_value = value
```

### Unions with `None`

Any union with `None` at the outermost level is ignored:

* `Optional[int]` will be parsed as `int`
* `Tuple[str, int, float] | None` will be parsed as `Tuple[str, int, float]`
* `Tuple[Optional[str], int, float] | None` is not allowed - the first element can be either a `str` or `None`, which
isn't possible to unambiguously parse.

### Tuples

Tuples are handled as comma-separated values. If you need to put a comma in a value itself, you can wrap it in quotes.

* `tuple[int, int, int]` would take in `1,2,3`
* `tuple[int, float, str]` would take in `1,3.14,etc`
* `tuple[int, ...]` - would not work, as flexible-length tuples are not allowed (though this may change in the future)
* `tuple[str, str]` would take in `'abc,"d,e,f"'`, which would become `("abc", "d,e,f")`

!!! note "Quote double-wrapping"
    To escape a comma, the whole argument must be wrapped in quotes - this is necessary to prevent your shell from
    parsing away the inner pair of quotes. Please discuss in [#7](https://github.com/treykeown/arguably/issues/7) if you
    have input on a better way of doing this.

### Lists

Lists are comma-separated, like `tuples`. However, if a list appears as an `--option`, it can be specified multiple
times.

* `list[int]` would take in `1,2,3,4`
* `def foo(*, bar: list[int])` would take in `--bar 1 --bar 2 --bar 3,4`

### `enum.Enum`

Enums allow member names to be used as input. No other value is accepted.

Enum names are normalized the same way as [function names](../subcommands/#name-normalization):

* Converted to lowercase
* `_leading` and `trailing__` underscores `_` are stripped
* Underscores `between_words` are converted to dashes: `between-words`

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/enum-1.py">[source]</a>
</sub></div>

```python
import arguably
import enum

class Direction(enum.Enum):
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

@arguably.command
def move(start: tuple[int, int], direction: Direction):
    end = start + direction.value
    print(f"{start=}", f"{direction}", f"{end=}")

if __name__ == "__main__":
    arguably.run()
```

```console
user@machine:~$ python3 enum-1.py 100,100 diagonally
usage: enum-1.py [-h] start,start {up,down,left,right}
enum-1.py: error: argument direction: invalid choice: 'diagonally' (choose from 'up', 'down', 'left', 'right')
```
```console
user@machine:~$ python3 enum-1.py 100,100 down
start=(100, 100) Direction.DOWN end=(100, 99)
```

### `enum.Flag`

Flag values never appear directly. Instead, each member always appears as an `--option`. The docstring for `enum.Flag`
values is parsed as well, meaning you can create help messages for each entry and specify a shorthand through `[-x]`.

Flag names are processed the same way as [`enum.Enum` names](#enumenum).

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/flag.py">[source]</a>
</sub></div>

```python
import arguably
import enum
from pathlib import Path

class Permissions(enum.Flag):
    """
    Permission flags

    Attributes:
        READ: [-r] allows for reads
        WRITE: [-w] allows for writes
        EXECUTE: [-x] allows for execution
    """

    READ = 4
    WRITE = 2
    EXECUTE = 1

class PermissionsAlt(enum.Flag):
    """Annotations can also appear like this"""

    READ = 4
    """[-r] allows for reads"""
    WRITE = 2
    """[-w] allows for writes"""
    EXECUTE = 1
    """[-x] allows for execution"""

@arguably.command
def chmod(file: Path, *, flags: Permissions = Permissions(0)):
    """
    change file permissions

    Args:
        file: the file to modify
        flags: permission flags
    """
    print(f"{file=}", f"{flags=}")

if __name__ == "__main__":
    arguably.run()
```
```console
user@machine:~$ python3 flag.py -h
usage: flag.py [-h] [-r] [-w] [-x] file

change file permissions

positional arguments:
  file           the file to modify (type: Path)

options:
  -h, --help     show this help message and exit
  -r, --read     allows for reads
  -w, --write    allows for writes
  -x, --execute  allows for execution
```
```console
user@machine:~$ python3 flag.py foo.txt -rwx
file=PosixPath('foo.txt') flags=<Permissions.READ|WRITE|EXECUTE: 7>
```

## Special behaviors

There are a number of special behaviors you can attach to a parameter. These utilize the ability to attach metadata to
a type using `typing.Annotated[]`:

```python
def foo(
    param: Annotated[<param_type>, arguably.arg.*()]
):
```

* [`arguably.arg.required()`](#arguablyargrequired) requires `list[]` and `*args` params to not be empty, or marks an
`--option` as required.
* [`arguably.arg.count()`](#arguablyargcount) counts the number of times an option appears: `-vvvv` gives `4`.
* [`arguably.arg.choices(*choices)`](#arguablyargchoices) restricts inputs to `choices`
* [`arguably.arg.missing(omit_value)`](#arguablyargmissing) `--option foo` yields `foo`, but this allows the value to be
omitted: just `--option` will use the given `omit_value`.
* [`arguably.arg.handler(func)`](#arguablyarghandler) skips all the argument processing `arguably` does and just calls
`func`
* [`arguably.arg.builder()`](#arguablyargbuilder) treats the input as instructions on how to build a class

### Example

Here's an example of each being used. This is all the same script, but results are shown after each example.

#### `arguably.arg.required`

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/annotated.py">[source]</a>
</sub></div>

```python
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
```

```console
user@machine:~$ python3 annotated.py email example@google.com
usage: annotated.py email [-h] from to [to ...]
annotated.py email: error: the following arguments are required: to
```
```console
user@machine:~$ python3 annotated.py email foo@example.com monty@python.org shrubbery-interest@example.com
from_='foo@example.com' to=('monty@python.org', 'shrubbery-interest@example.com')
```

#### `arguably.arg.count`
```python
@arguably.command
def process(
    *,
    verbose: Annotated[int, arguably.arg.count()],
):
    """
    :param verbose: [-v] verbosity
    """
    print(f"{verbose=}")
```

```console
user@machine:~$ python3 annotated.py process -vvvv
verbose=4
```

#### `arguably.arg.choices`
```python
@arguably.command
def move(
    direction: Annotated[str, arguably.arg.choices("left", "right", "up", "down")]
):
    """An enum is usually recommended for cases like this"""
    print(f"{direction=}")
```

```console
user@machine:~$ python3 annotated.py move diagonally
usage: annotated.py move [-h] {left,right,up,down}
annotated.py move: error: argument direction: invalid choice: 'diagonally' (choose from 'left', 'right', 'up', 'down')
```

#### `arguably.arg.missing`
```python
@arguably.command
def do_something(
    *,
    log: Annotated[Path | None, arguably.arg.missing("~/.log.txt")] = None
):
    print(f"{log=}")
```

```console
user@machine:~$ python3 annotated.py do-something
log=None
```
```console
user@machine:~$ python3 annotated.py do-something --log
log=PosixPath('~/.log.txt')
```
```console
user@machine:~$ python3 annotated.py do-something --log here.log
log=PosixPath('here.log')
```

#### `arguably.arg.handler`
```python
@arguably.command
def handle_it(
    version: Annotated[int, arguably.arg.handler(lambda s: int(s.split("-")[-1]))] = None
):
    print(f"{version=}")
```

```console
user@machine:~$ python3 annotated.py handle-it python-3
version=3
```

#### `arguably.arg.builder`
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
def builder(
    *,
    nic: Annotated[list[Nic], arguably.arg.builder()]
):
    print(f"{nic=}")
```

```console
user@machine:~$ python3 annotated.py builder --nic tap,model=e1000 --nic user,hostfwd=tcp::10022-:22
nic=[TapNic(model='e1000'), UserNic(hostfwd='tcp::10022-:22')]
```

```python
if __name__ == "__main__":
    arguably.run()
```
