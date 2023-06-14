<p align="center">
      <img alt="arguably logo" src="https://raw.githubusercontent.com/treykeown/arguably/main/etc/logo/arguably_black.png">
</p>

<p align="center">
    <em>
        The best Python CLI library, arguably.
    </em>
</p>

<p align="center">
    <a href="https://github.com/treykeown/arguably/actions/workflows/python-package.yml"><img src="https://github.com/treykeown/arguably/actions/workflows/python-package.yml/badge.svg" alt="Test status"></a>
    <a href="https://treykeown.github.io/arguably/coverage/"><img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/treykeown/f493b14288af4e8358ea8578c393213a/raw/arguably-coverage-badge.json" alt="Code coverage"></a>
    <a href="https://pypi.org/project/arguably/"><img src="https://shields.io/pypi/pyversions/arguably" alt="Supported Python versions"></a>
    <a href="https://pypi.org/project/arguably/"><img src="https://shields.io/pypi/v/arguably" alt="PyPI version"></a>
</p>
<hr>

`arguably` turns functions into command line interfaces. `arguably` has a tiny API and is extremely easy to integrate.
You can also use it directly through `python3 -m arguably your_script.py`, more on that
[here](#no-integration-required)

To use `arguably` in a script, decorate any functions that should appear on the command line with `@arguably.command`,
then call `arguably.run()`. If multiple functions are decorated, they'll all appear as subcommands. You can even have
multiple levels of subcommands.

```python
@arguably.command
def some_function(required, not_required=2, *others: int, option: float = 3.14):
    """
    this function is on the command line!
    :param required: a required parameter
    :param not_required: this one isn't required, since it has a default
    :param others: all the other positional arguments go here
    :param option: [-x] an option, short name is in brackets
    """
    ...
```

<p align="center"><b><em>becomes</em></b></p>

```console
user@machine:~$ ./some_script.py -h
usage: some_script.py [-h] [-x OPTION] required [not-required] [others ...]

this function is on the command line!

positional arguments:
  required             a required parameter (type: str)
  not-required         this one isn't required, since it has a default (type: int, default: 2)
  others               all the other positional arguments go here (type: int)

options:
  -h, --help           show this help message and exit
  -x, --option OPTION  an option, short name is in brackets (type: float, default: 3.14)
```

`arguably` looks at any decorated functions and maps them from a Python to the CLI exactly how you would expect:

| This Python ...                                | ... becomes this on the CLI.                   |
|------------------------------------------------|------------------------------------------------|
| positional args, no default `required`         | positional CLI args, required `required`       |
| positional args, with default `not_required=2` | positional CLI args, optional `[not-required]` |
| positional args, variadic `*others`            | any extra positional CLI args `[others ...]`   |
| keyword-only arguments `option`                | command-line options `[-x OPTION]`             |

Type annotations are optional, but `arguably` can use them to automatically convert arguments to their type. It has
smart handling for `tuple`, `list`, `enum.Enum`, and `enum.Flag`. There are also a few special behaviors you can attach
to a parameter via `Annotated[]` and the `arguably.arg.*` functions. Using `arguably.arg.builder()`, you can even
build an object to pass in from the command line (using syntax inspired by QEMU):

```console
user@machine:~$ ./script.py --nic tap,model=e1000 --nic user,hostfwd=tcp::10022-:22
nic=[TapNic(model='e1000'), UserNic(hostfwd='tcp::10022-:22')]
```

## No integration required

Don't want to write any code? Simply pass any Python script to `arguably` to give it a command line interface.

```console
user@machine:~$ python3 -m arguably party-trick.py
usage: party-trick [-h] command ...

positional arguments:
  command
    hello                this is the docstring for a function in the script
    goodbye              any function from a script can be called
    a-class              so can any __init__ for objects defined in the script
    a-class.func-static  a @staticmethod on a class can be called
    a-class.func-cls     so can a @classmethod

options:
  -h, --help             show this help message and exit
```

## Documentation

The full documentation can be found here: [https://treykeown.github.io/arguably/](https://treykeown.github.io/arguably/)

* Get Started: [https://treykeown.github.io/arguably/get-started/](https://treykeown.github.io/arguably/get-started/)
* API Reference: [https://treykeown.github.io/arguably/api-reference/](https://treykeown.github.io/arguably/api-reference/)

## Dependencies

All of `arguably` is built on top of `argparse`. It has two dependencies:

* `docstring-parser` for parsing function docstrings
* `typing-extensions` for `Annotated[]` support in Python 3.8 (only needed for that version)

## Installation

Install using `pip install arguably`. If you want to install by using `conda`, please comment on
[this issue](https://github.com/treykeown/arguably/issues/12).

## Future Roadmap

If you have any interest in these (either as a user or implementer), please leave a comment!

* [#8 - Display all enum options in a command group](https://github.com/treykeown/arguably/issues/8)
* [#9 - Both positive and negative boolean flags](https://github.com/treykeown/arguably/issues/9)
* [#10 - Take inputs from environment variables](https://github.com/treykeown/arguably/issues/10)
* [#13 - Load configuration for a script via a `.yml`](https://github.com/treykeown/arguably/issues/13)