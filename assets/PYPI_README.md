<p align="center">
      <img alt="arguably logo" src="https://raw.githubusercontent.com/treykeown/arguably/main/assets/arguably_black.png">
</p>

<p align="center">
    <em>
        the best CLI library, arguably<br>
        turns your functions into command line interfaces
    </em>
</p>

<p align="center">
    <a href="https://github.com/treykeown/arguably/actions/workflows/python-package.yml"><img src="https://github.com/treykeown/arguably/actions/workflows/python-package.yml/badge.svg" alt="Test status"></a>
    <a href="https://treykeown.github.io/arguably/coverage/"><img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/treykeown/f493b14288af4e8358ea8578c393213a/raw/arguably-coverage-badge.json" alt="Code coverage"></a>
    <a href="https://pypi.org/project/arguably/"><img src="https://shields.io/pypi/pyversions/arguably" alt="Supported Python versions"></a>
    <a href="https://pypi.org/project/arguably/"><img src="https://shields.io/pypi/v/arguably" alt="PyPI version"></a>
</p>
<hr>

`arguably` solves this problem:
1. You've written a Python script
2. Now you want to pass in parameters from the command line
3. You don't want to read the docs for your favorite argument parsing library *again*

By leveraging as many Python idioms as possible, `arguably` keeps its API small and memorable without sacrificing
functionality. `arguably` uses functions and their docstrings to automatically set up argparse. Notably, `arguably`
maps your function signature to a command-line interface like this:

```python
@arguably.command
def some_function(required, not_required="foo", *others, option="bar"):
    ...
```

<p align="center"><b><em>becomes</em></b></p>

```text
usage: script [--option OPTION] required [not-required] [others ...]
```

In short, `arguably` turns your function's **positional parameters** into **positional command-line arguments**, and
your function's **keyword-only arguments** into **command-line options**. From the example above:

| Name           | Type                                | Becomes                         | Usage               |
|----------------|-------------------------------------|---------------------------------|---------------------|
| `required`     | positional, no default value        | required positional arg         | `required`          |
| `not_required` | positional, with default value      | optional positional arg         | `[not-required]`    |
| `others`       | positional, variadic (like `*args`) | the rest of the positional args | `[others ...]`      |
| `option`       | keyword-only argument               | an option                       | `[--option OPTION]` |

`arguably` also enables you to easily add subcommands - just annotate more than one function with `@arguably.command`.
You can even have nested subcommands (more on that later).

`arguably` reads type annotations and automatically converts arguments to the declared types. It has smart handling for
`tuple`, `list`, `enum.Enum`, and `enum.Flag`. There are also a few special behaviors you can attach to a parameter
via `Annotated[]` and the `arguably.arg.*` functions.

`arguably` parses docstrings to generate descriptions for your commands and parameters. If you want to give a parameter
the alias `-X`, prefix its docstring description with `[-X]`. Wrapping a word in `{}` changes the *metavar* that gets
printed (this is what's shown in the usage string after an option name, don't worry if you aren't familiar with this).
For example:

```python
#!/usr/bin/env python3
"""docstrings for the file become the description for the script."""
__version__ = "1.0.0"  # You can also set `version_flag=True` to add a version flag, it will read `__version__`

import arguably

@arguably.command(alias="h")
def hello(name: str, *, lastname: str | None = None):
    """
    says hello to you
    :param name: your name
    :param lastname: [-l] your {surname}
    """
    full_name = name if lastname is None else f"{name} {lastname}"
    print(f"Hello, {full_name}!")

@arguably.command(alias="g")
def goodbye(name: str, *, is_sad: bool = False):
    """
    says goodbye to you
    :param name: your name
    :param is_sad: [-s] whether or not it's sad to see you go
    """
    print(f"Goodbye, {name}!")
    if is_sad:
        print(f"It's sad to see you go!")

if __name__ == "__main__":
    arguably.run(version_flag=True)
```

<p align="center"><b><em>becomes</em></b></p>

```console
user@machine:~$ python3 script.py
usage: test_scripts.docs2 [-h] [--version] command ...

docstrings for the file become the description for the script.

positional arguments:
  command
    hello (h)    says hello to you
    goodbye (g)  says goodbye to you

options:
  -h, --help     show this help message and exit
  --version      show program's version number and exit


user@machine:~$ python3 script.py hello --help
usage: test_scripts.docs2 hello [-h] [-l SURNAME] name

says hello to you

positional arguments:
  name                    your name

options:
  -h, --help              show this help message and exit
  -l, --lastname SURNAME  your surname (default: None)
```

More docs coming soon...
