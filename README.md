<p align="center">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/treykeown/arguably/main/assets/arguably_white.png">
      <img alt="arguably logo" src="https://raw.githubusercontent.com/treykeown/arguably/main/assets/arguably_black.png">
    </picture>
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
You can even use it to run functions and class methods directly from a script, without even integrating it - just run
`python3 -m arguably your_script.py`.

To use `arguably` in a script, just decorate any functions that should appear on the command line with
`@arguably.command`, then call `arguably.run()`. If multiple functions are decorated, they'll all appear as subcommands.
You can even have [multiple levels of subcommands](#FIXME).

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

```text
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

`arguably` looks at any decorated functions and transforms them like this:

* positional arguments &rightarrow; positional command-line arguments
* keyword-only arguments &rightarrow; command-line options
* type annotations (or type of default value) &rightarrow; type of the argument
* parameter docstring &rightarrow; help for the argument

Type annotations are optional, but `arguably` can use them to automatically convert arguments to their type. It has
smart handling for `tuple`, `list`, `enum.Enum`, and `enum.Flag`. There are also a few special behaviors you can attach
to a parameter via `Annotated[]` and the `arguably.arg.*` functions, [documented here](#FIXME). Using
`arguably.arg.builder()`, you can even build an object to pass in from the command line (using syntax inspired by QEMU):

```console
user@machine:~$ ./script.py --nic tap,model=e1000 --nic user,hostfwd=tcp::10022-:22
nic=[TapNic(model='e1000'), UserNic(hostfwd='tcp::10022-:22')]
```

Install with `pip install arguably`, check out the [maximalist script](#TODO) to see all features being used, and check
the full documentation below.

## API Reference

`arguably` tries to keep its API tiny but full-featured. Here's a brief rundown of **everything**:
* `@arguably.command` marks a function so that it appears in the command line interface. If multiple functions
are marked, they'll each appear as subcommands.
* `arguably.run(...)` parses the command-line arguments and runs your decorated function. If you need to configure
anything about `arguably`, you pass in a keyword argument here.
* `arguably.error()` prints an error to the console and exits the script.
* `arguably.is_target()` is only useful if you have layers of subcommands. It returns `True` if the currently running
function was the targeted command, and `False` if it's just an ancestor. For example, if a user specifies the command
`git remote add`, this returns `False` for `git()` and `git__remote()`, but `True` for `git__remote__add()`.
* `@arguably.subtype(alias="...")` marks a class so that it can be built by `arguably.arg.builder()`.
* `arguably.arg` contains a few special behaviors you can attach to an argument through `Annotated[]`.
  * `arguably.arg.required()` explicitly marks a parameter as required. Only needed if you want at least one item in
  `*args`, or if you want to make an `--option` required.
  * `arguably.arg.count()` counts the number of times an option is passed in. For example, with `-v/--verbose` passing
  in `-vvvv` would yield `4`
  * `arguably.arg.choices(...)` explicity specifies choices for an argument. Not required if your argument's type is an
  `enum.Enum`.
  * `arguably.arg.missing(val)` will use `val` if an option is specified, but no value is given for it.
  * `arguably.arg.handler(func)` will skip all processing by `arguably`, and call `func` to process an input
  * `arguably.arg.builder()` will build a class (or one of its subclasses marked with `@arguably.subtype`)

Full details to come...
