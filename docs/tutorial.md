# Tutorial

## Introduction

The two most important things to know:

* `@arguably.command` marks a function to appear on the CLI
* `arguably.run()` parses the CLI arguments and calls the marked functions

There are three other functions exposed by `arguably`, as well as six special behaviors you can attach to an argument.
More on those later.

### Hello, world!

First, a "Hello, world!" script:

```python
import arguably

@arguably.command
def hello(name):
    print(f"Hello, {name}!")

if __name__ == "__main__":
    arguably.run()
```
```console
user@machine:~$ python3 hello-1.py Python
Hello, Python!

user@machine:~$ python3 hello-1.py -h
usage: hello-1.py [-h] name

positional arguments:
  name        (type: str)

options:
  -h, --help  show this help message and exit
```

`arguably` detected that the `hello()` function has a single argument called `name`. Because `name` is a required
argument for the `hello()` function, it's also a required argument on the CLI. If the script is run without giving a
`name`, it prints a message stating that the argument is required:

```console
user@machine:~$ python3 hello-1.py
usage: hello-1.py [-h] name
hello-1.py: error: the following arguments are required: name
```

### Optional arguments

To make `name` optional on the CLI, make it optional in Python - give it a default value.

```python
@arguably.command
def hello(name="world"):
    print(f"Hello, {name}!")
```
```console
user@machine:~$ python3 hello-2.py
Hello, world!

user@machine:~$ python3 hello-2.py Python
Hello, Python!

user@machine:~$ python3 hello-2.py -h
usage: hello-2.py [-h] [name]

positional arguments:
  name        (type: str, default: world)

options:
  -h, --help  show this help message and exit
```

### Adding an `[--option]`

To make `name` an `--option` instead of a positional argument, turn it into a [keyword-only argument](https://docs.python.org/3/tutorial/controlflow.html#keyword-only-arguments).
If you've ever seen `*args`, this should be familiar. The `*` symbolizes taking in all extra positional arguments. If
you're not expecting any extra positional arguments, just put `*`.

```python
@arguably.command
def hello(*, name="world"):
    print(f"Hello, {name}!")
```
```pycon
>>> @arguably.command
... def hello(*, name="world"):
...     print(f"Hello, {name}!")
...
>>> hello()
Hello, world!
>>> hello("Python")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: hello() takes 0 positional arguments but 1 was given
>>> hello(name="Python")
Hello, Python!
```
```console
user@machine:~$ python3 hello-3.py -h
usage: hello-3.py [-h] [--name NAME]

options:
  -h, --help   show this help message and exit
  --name NAME  (type: str, default: world)

user@machine:~$ python3 hello-3.py --name Python
Hello, Python!
```

### Adding help messages

To add help messages to parameters, add a docstring. It can be any of the major formats: reStructuredText (Sphinx),
Google, Numpydoc, or Epydoc. We'll use Google's style for this example.

```python
@arguably.command
def hello(*, name="world"):
    """
    this will say hello to someone

    Args:
        name: is who this will greet
    """
    print(f"Hello, {name}!")
```
```console
user@machine:~$ python3 hello-4.py -h
usage: hello-4.py [-h] [--name NAME]

this will say hello to someone

options:
  -h, --help   show this help message and exit
  --name NAME  is who this will greet (type: str, default: world)
```

#### Help message directives

There are two special things you can put in your docstring that `arguably` will use.

| Format          | Applies to...   | Function                     |
|-----------------|-----------------|------------------------------|
| `[-n] ...`      | `--option` only | Short name for an `--option` |
| `... {WHO} ...` | any argument    | Metavar for an argument      |

If you're not familiar with a metavar, that's the term for what gets printed in the usage string for the user-provided
value. More explanation for that [here](https://docs.python.org/3/library/argparse.html#metavar).

```python
@arguably.command
def hello(*, name="world"):
    """
    this will say hello to someone

    Args:
        name: [-n] is {who} this will greet
    """
    print(f"Hello, {name}!")
```
```console
user@machine:~$ python3 hello-5.py -h
usage: hello-5.py [-h] [-n WHO]

this will say hello to someone

options:
  -h, --help      show this help message and exit
  -n, --name WHO  is who this will greet (type: str, default: world)
```

Compare the last line with how it was before:

```console
Before:  --name NAME     is who this will greet (type: str, default: world)
After:   -n, --name WHO  is who this will greet (type: str, default: world)
```

### Taking in many arguments

To take in a variable number of positional arguments, use the `*args` syntax (as mentioned [above](#adding-an-option)).

```python
import arguably

@arguably.command
def process(*files):
    """
    process many files

    Args:
        files: the {file}s to process
    """
    for file in files:
        print(f"Processing {file}...")

if __name__ == "__main__":
    arguably.run()
```
```console
user@machine:~$ python3 process-1.py -h
usage: process-1.py [-h] [FILE ...]

process many files

positional arguments:
  FILE        the files to process (type: str)

options:
  -h, --help  show this help message and exit

user@machine:~$ python3 process-1.py report-1.csv report-2.csv report-3.csv
Processing report-1.csv...
Processing report-2.csv...
Processing report-3.csv...
```

To require at least one input to `*args`, [see here](#TODO)

## Subcommands

Marking multiple functions with `@arguably.command` will make them show up as subcommands on the CLI:

```python
import arguably

@arguably.command
def hello(name):
    """this will say hello to someone"""
    print(f"Hello, {name}!")

@arguably.command
def goodbye(name):
    """this will say goodbye to someone"""
    print(f"Goodbye, {name}!")

if __name__ == "__main__":
    arguably.run()
```
```console
user@machine:~$ python3 goodbye-1.py -h
usage: goodbye-1.py [-h] command ...

positional arguments:
  command
    hello     this will say hello to someone
    goodbye   this will say goodbye to someone

options:
  -h, --help  show this help message and exit

user@machine:~$ python3 goodbye-1.py hello Python
Hello, Python!

user@machine:~$ python3 goodbye-1.py goodbye Python
Goodbye, Python!
```

Note that single underscores `_` in a function name are converted to a dash `-`. Also, any leading or trailing
underscores are stripped.

* `def foo_bar():` &rightarrow; `foo-bar`
* `def list_():` &rightarrow; `list`
* `def _asdf():` &rightarrow; `asdf`
* `def __foo__():` &rightarrow; `foo`
* `def ___really_really_long_name():` &rightarrow; `really-really-long-name`

### Multi-level subcommands

Making multi-level subcommands is easy. To add a subcommand to a parent command, separate their names with two
underscores `__`. So `s3__ls` becomes `s3 ls`, and `ec2__start_instances` becomes `ec2 start-instances`. Using these
[S3](https://docs.aws.amazon.com/cli/latest/reference/s3/#synopsis) and [EC2](https://docs.aws.amazon.com/cli/latest/reference/ec2/start-instances.html#examples)
commands for the AWS CLI as an example:

```python
import arguably

@arguably.command
def ec2__start_instances(*instances):
    """
    start instances
    Args:
        *instances: {instance}s to start
    """
    for inst in instances:
        print(f"Starting {inst}")

@arguably.command
def ec2__stop_instances(*instances):
    """
    stop instances
    Args:
        *instances: {instance}s to stop
    """
    for inst in instances:
        print(f"Stopping {inst}")

@arguably.command
def s3__ls(path="/"):
    """
    list objects
    Args:
        path: path to list under
    """
    print(f"Listing objects under {path}")

@arguably.command
def s3__cp(src, dst):
    """
    copy objects
    Args:
        src: source object
        dst: destination path
    """
    print(f"Copy {src} to {dst}")

if __name__ == "__main__":
    arguably.run()
```
```console
user@machine:~$ python3 aws-1.py -h
usage: aws-1.py [-h] command ...

positional arguments:
  command
    ec2
    s3

options:
  -h, --help  show this help message and exit

user@machine:~$ python3 aws-1.py s3 -h
usage: aws-1.py s3 [-h] command ...

positional arguments:
  command
    ls        list objects
    cp        copy objects

options:
  -h, --help  show this help message and exit

user@machine:~$ python3 aws-1.py s3 ls -h
usage: aws-1.py s3 ls [-h] [path]

list objects

positional arguments:
  path        path to list under (type: str, default: /)

options:
  -h, --help  show this help message and exit

user@machine:~$ python3 aws-1.py s3 ls /foo/bar
Listing objects under /foo/bar
```

#### Hierarchy

You may have noticed that `ec2` and `s3` had no description. This is because they are automatically created stubs. We
can define them ourselves and attach arguments to them:

```python
@arguably.command
def s3(*, bucket):
    """
    s3 commands
    Args:
        bucket: the bucket to use
    """
    print(f"Using bucket: {bucket}")
```
```console
user@machine:~$ python3 aws-2.py s3 -h
usage: aws-2.py s3 [-h] [--bucket BUCKET] command ...

s3 commands

positional arguments:
  command
    ls             list objects
    cp             copy objects

options:
  -h, --help       show this help message and exit
  --bucket BUCKET  the bucket to use (type: str)

user@machine:~$ python3 aws-2.py s3 --bucket mybucket ls
Using bucket: mybucket
Listing objects under /
```

As you can see, `def s3(*, bucket)` was called first and printed the bucket name to use. After that,
`def s3__ls(path="/")` was invoked. This is because all ancestors are invoked before the target command is invoked. For
a more complex example:

```python
import arguably

@arguably.command
def first():
    print("first")

@arguably.command
def first__second():
    print("second")

@arguably.command
def first__second__third():
    print("third")

if __name__ == "__main__":
    arguably.run(always_subcommand=True)
```
```console
user@machine:~$ python3 nested-1.py first second third
first
second
third
```

### The `__root__` function

If a function named `__root__` is marked with `@arguably.command`, it always appears as the highest ancestor for
commands in the script. This allows global options and actions to be placed at the root of the script.

```python
import arguably

@arguably.command
def __root__():
    print("__root__")

@arguably.command
def hi():
    print("hi")

@arguably.command
def bye():
    print("bye")

if __name__ == "__main__":
    arguably.run()
```
```console
user@machine:~$ python3 root-1.py hi
__root__
hi
```

### Checking `arguably.is_target()`

Sometimes you'll want to allow a command in the heirarchy to process its input arguments, but bail if it wasn't the
target. For that, you can use `arguably.is_target()`. This returns `False` if the currently-executing function was
called as an ancestor of the target command, and `True` every other time.

```python
import arguably

@arguably.command
def __root__(*, config_file=None):
    print(f"Using config {config_file}")
    if not arguably.is_target():
        return
    print("__root__ is the target!")

@arguably.command
def hi():
    print("hi is the target!")

@arguably.command
def bye():
    print("bye is the target!")

if __name__ == "__main__":
    arguably.run()
```
```console
user@machine:~$ python3 root-2.py --config-file foo.yml
Using config foo.yml
__root__ is the target!

user@machine:~$ python3 root-2.py --config-file foo.yml hi
Using config foo.yml
hi is the target!
```

## Type hints

`arguably` uses type hints to convert from text passed in by the CLI to the class needed by your functions.

```python
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
```
```console
user@machine:~$ python3 type-hint.py basic Monty 42 33.3
name='Monty' age=42 percent=33.3

user@machine:~$ python3 type-hint.py tuple foo,1,3.14
value=('foo', 1, 3.14)

user@machine:~$ python3 type-hint.py any-type 123 .
value=UserType(val=123) path=PosixPath('.')

user@machine:~$ python3 type-hint.py list foo.txt,bar.exe --nums 1 --nums 2,3
files=[PosixPath('foo.txt'), PosixPath('bar.exe')] nums=[1, 2, 3]
```

Allowed types are:

* Any type that can be constructed by passing in a single string value. This includes:
  * Basic built-in types like `str`, `int`, `float`, `bool`
  * Other built-ins like `pathlib.Path`
  * Any user-defined classes that also have this kind of constructor
* `enum.Enum` and `enum.Flag` - values are referenced by the lowercased name
  * The docstring for `enum.Flag` values is parsed as well, meaning you can create help messages for each entry and
  specify a shorthand through `[-x]`
* `Optional[some_type]` / `some_type | None` - any union with `None` is ignored, so this would be parsed as `some_type`
* `tuple[int, float, etc]` - handled as comma-separated values `1,3.14,etc`
* `list[some_type]` - handled as comma-separated values if positional, but can be specified multiple times as an option

### `enum.Enum`

Enums are processed to allow each of the member names to be input, but no other values.

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

user@machine:~$ python3 enum-1.py 100,100 down
start=(100, 100) Direction.DOWN end=(100, 99)
```

### `enum.Flag`

Flag values never appear directly. Instead, each member always appears as an `--option`.

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

user@machine:~$ python3 flag.py foo.txt -rwx
file=PosixPath('foo.txt') flags=<Permissions.READ|WRITE|EXECUTE: 7>
```

### Special behaviors

There are a number of special behaviors you can attach to a parameter. These utilize the ability to attach metadata to
a type using `typing.Annotated[]`:

```python
def foo(
    param: Annotated[<param_type>, arguably.arg.*()]
):
```

* [`arguably.arg.required()`](#arguably.arg.required) requires `list[]` and `*args` params to not be empty, or marks an
`--option` as required.
* [`arguably.arg.count()`](#arguably.arg.count) counts the number of times an option appears: `-vvvv` gives `4`.
* [`arguably.arg.choices(*choices)`](#arguably.arg.choices) restricts inputs to `choices`
* [`arguably.arg.missing(omit_value)`](#arguably.arg.missing) `--option foo` yields `foo`, but this allows the value to
be omitted: just `--option` will use the given `omit_value`.
* [`arguably.arg.handler(func)`](#arguably.arg.handler) skips all the argument processing `arguably` does and just calls
`func`
* [`arguably.arg.builder()`](#arguably.arg.builder) treats the input as instructions on how to build a class

#### Example

Here's an example of each being used

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

# The following lines are for arguably.arg.builder()
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
```
```console
user@machine:~$ python3 annotated.py email example@google.com
usage: annotated.py email [-h] from to [to ...]
annotated.py email: error: the following arguments are required: to

user@machine:~$ python3 annotated.py email foo@example.com monty@python.org shrubbery-interest@example.com
from_='foo@example.com' to=('monty@python.org', 'shrubbery-interest@example.com')

user@machine:~$ python3 annotated.py process -vvvv
verbose=4

user@machine:~$ python3 annotated.py move diagonally
usage: annotated.py move [-h] {left,right,up,down}
annotated.py move: error: argument direction: invalid choice: 'diagonally' (choose from 'left', 'right', 'up', 'down')

user@machine:~$ python3 annotated.py do-something
log=None

user@machine:~$ python3 annotated.py do-something --log
log=PosixPath('~/.log.txt')

user@machine:~$ python3 annotated.py do-something --log here.log
log=PosixPath('here.log')

user@machine:~$ python3 annotated.py handle-it python-3
version=3

user@machine:~$ python3 annotated.py builder --nic tap,model=e1000 --nic user,hostfwd=tcp::10022-:22
nic=[TapNic(model='e1000'), UserNic(hostfwd='tcp::10022-:22')]
```
