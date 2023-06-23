# Why `arguably`?

With plenty of other tools out there, why use `arguably`? Aren't other ones (`click`, `typer`, etc) good enough?

The short answer is: yeah, probably! Python already has great tools for building CLIs. But they still make you write
quite a bit of code. That's where `arguably` comes in.

## An unobtrusive API

What `arguably` does best is get out of your way.

Set up a *function signature* and *docstring*, annotate with `@arguably.command`, and you've set up a CLI. That's it,
that's the API.

No need for `typer.Option()` or `click.option()`. That's because `arguably` was built from the ground-up with a focus on
providing most of the features of these libraries (and a few extra) with few code changes necessary on your part.
Because of this, your CLI functions still look and behave like regular functions.

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/intro.py">[source]</a>
</sub></div>

```python
#!/usr/bin/env python3
import arguably

@arguably.command
def some_function(required, not_required=2, *others: int, option: float = 3.14):
    """
    this function is on the command line!

    Args:
        required: a required argument
        not_required: this one isn't required, since it has a default value
        *others: all the other positional arguments go here
        option: [-x] keyword-only args are options, short name is in brackets
    """
    print(f"{required=}, {not_required=}, {others=}, {option=}")

if __name__ == "__main__":
    arguably.run()
```

```console
user@machine:~$ ./intro.py -h
usage: intro.py [-h] [-x OPTION] required [not-required] [others ...]

this function is on the command line!

positional arguments:
  required             a required argument (type: str)
  not-required         this one isn't required, since it has a default value (type: int, default: 2)
  others               all the other positional arguments go here (type: int)

options:
  -h, --help           show this help message and exit
  -x, --option OPTION  keyword-only args are options, short name is in brackets (type: float, default: 3.14)
```

```pycon
>>> from intro import some_function
>>> some_function("asdf", 0, 7, 8, 9, option=2.71)
required='asdf', not_required=0, others=(7, 8, 9), option=2.71
```

```console
user@machine:~$ ./intro.py "asdf" 0 7 8 9 --option 2.71
required='asdf', not_required=0, others=(7, 8, 9), option=2.71
```

## Zero-effort CLI

Taking inspiration from [Python Fire](https://google.github.io/python-fire/guide/#version-4-fire-without-code-changes),
`arguably` is also able to execute your script directly, requiring *no* code changes - just run
`python3 -m arguably your_script.py` to expose all functions (and your class `@classmethod`, `@staticmethod`, and
`__init__` methods) on the CLI.

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/party-trick.py">[source]</a>
</sub></div>

```python
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
```

```console
user@machine:~$ python3 -m arguably party-trick.py -h
usage: party-trick [-h] [--version] command ...

this is the docstring for the whole script

positional arguments:
  command
    hello                   this is hello's docstring
    goodbye                 any function from a script can be called
    some-class              so can any __init__ for objects defined in the script
    some-class.func-static  a @staticmethod on a class can be called
    some-class.func-cls     so can a @classmethod

options:
  -h, --help                show this help message and exit
  --version                 show program's version number and exit
```

```console
user@machine:~$ python3 -m arguably party-trick.py hello -h
usage: party-trick hello [-h] name

this is hello's docstring

positional arguments:
  name        argument docstrings are automatically used (type: str)

options:
  -h, --help  show this help message and exit
```

```console
user@machine:~$ python3 -m arguably party-trick.py hello world
Hello, world!
```

## A comparison with `typer`

A quick comparison with a `typer` CLI is below. This is taken from the
[`databooks` project](https://github.com/datarootsio/databooks).

!!! warning
    The design for the config interface shown here for `arguably` isn't yet finalized and is still being implemented.
    Development is tracked in [https://github.com/treykeown/arguably/issues/13](https://github.com/treykeown/arguably/issues/13).

### The `typer` implementation

<div align="right" class="code-source"><sub>
    <a href="https://github.com/datarootsio/databooks/blob/39badd2c9cbdfa9a3174447948e6d65d78cb810f/databooks/cli.py#L378C36-L415">[source]</a>
</sub></div>

```python
app = Typer()

...

@app.command(add_help_option=False)
def show(
    paths: List[Path] = Argument(
        ..., is_eager=True, help="Path(s) of notebook files with conflicts"
    ),
    ignore: List[str] = Option(["!*"], help="Glob expression(s) of files to ignore"),
    export: Optional[ImgFmt] = Option(
        None,
        "--export",
        "-x",
        help="Export rich outputs as a string.",
    ),
    pager: bool = Option(
        False, "--pager", "-p", help="Use pager instead of printing to terminal"
    ),
    verbose: bool = Option(
        False, "--verbose", "-v", help="Increase verbosity for debugging"
    ),
    multiple: bool = Option(False, "--yes", "-y", help="Show multiple files"),
    config: Optional[Path] = Option(
        None,
        "--config",
        "-c",
        is_eager=True,
        callback=_config_callback,
        resolve_path=True,
        exists=True,
        help="Get CLI options from configuration file",
    ),
    help: Optional[bool] = Option(
        None,
        "--help",
        is_eager=True,
        callback=_help_callback,
        help="Show this message and exit",
    ),
) -> None:
    """Show rich representation of notebook."""
    ...

...

app(prog_name="databooks")
```

### Rewritten with `arguably`

```python
@arguably.command
def show(
    *paths: Path,
    ignore: List[str] = ["!*"],
    export: Optional[ImgFmt] = None,
    pager: bool = False,
    verbose: bool = False,
    multiple: bool = False,
) -> None:
    """
    Show rich representation of notebook.
    Args:
        *paths: Path(s) of notebook files with conflicts
        ignore: Glob expression(s) of files to ignore
        export: [-x] Export rich outputs as a string.
        pager: [-p] Use pager instead of printing to terminal
        verbose: [-v] Increase verbosity for debugging
        multiple: [-y/--yes] Show multiple files
    """
    if ignore is None:
        ignore =   # Mutable argument defaults are bad
    ...

...

arguably.run(name="databooks", version_flag=True, config_flag=("-c", "--config"))
```

* `--help` is eagerly evaluated by default in `arguably`, so no separate argument is required.
* Aliases for options appear first in the docstring, like `[-x]` for `export`.
* The function still looks and behaves the same:
    * No need to assign `typer.Option()` as the default value for parameters
    * No need to put `Annotated[]` as your argument type, except in
    [special cases](../tutorial/type-hints/#special-behaviors).

`arguably` doesn't currently cover all the features that other frameworks do. It's designed with a focus on a minimal
API covering *most* use cases for *most* CLIs.
