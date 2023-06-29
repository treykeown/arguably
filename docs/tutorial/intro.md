# Introduction

When it comes to `arguably`, the most important things to know are:

* `@arguably.command` makes a function appear on the CLI
* `arguably.run()` parses the CLI arguments and calls the decorated functions

## Hello, world!

Here's a simple "Hello, world!" script:

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/hello-1.py">[source]</a>
</sub></div>

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
```
```console
user@machine:~$ python3 hello-1.py -h
usage: hello-1.py [-h] name

positional arguments:
  name        (type: str)

options:
  -h, --help  show this help message and exit
```

Because `name` is a required argument for the `hello()` function, it's also a required argument on the CLI. If the
script is run without giving a `name`, it prints a message stating that the argument is required:

```console
user@machine:~$ python3 hello-1.py
usage: hello-1.py [-h] name
hello-1.py: error: the following arguments are required: name
```

!!! note
    If desired, `async` functions are also supported.
    <div align="right" class="code-source"><sub>
        <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/hello-async-1.py">[source]</a>
    </sub></div>
    ```python
    import arguably
    import asyncio

    @arguably.command
    async def hello(name):
        await asyncio.sleep(1)
        print(f"Hello, {name}!")

    if __name__ == "__main__":
        arguably.run()
    ```
    ```console
    user@machine:~$ python3 hello-async-1.py Python
    Hello, Python!
    ```

## Optional arguments

To make an argument optional, give it a default value.

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/hello-2.py">[source]</a>
</sub></div>

```python
@arguably.command
def hello(name="world"):
    print(f"Hello, {name}!")
```

```console
user@machine:~$ python3 hello-2.py
Hello, world!
```
```console
user@machine:~$ python3 hello-2.py Python
Hello, Python!
```
```console
user@machine:~$ python3 hello-2.py -h
usage: hello-2.py [-h] [name]

positional arguments:
  name        (type: str, default: world)

options:
  -h, --help  show this help message and exit
```

## Adding an `[--option]`

To make an `--option` instead of a positional argument, use [keyword-only arguments](https://docs.python.org/3/tutorial/controlflow.html#keyword-only-arguments).
These are the arguments that appear after the `*` in the parameter list.

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/hello-3.py">[source]</a>
</sub></div>

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
```
```console
user@machine:~$ python3 hello-3.py --name Python
Hello, Python!
```

## Flexible number of args

To take in a variable number of positional arguments, use `*args`:

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/hello-4.py">[source]</a>
</sub></div>

```python
import arguably

@arguably.command
def hello(*from_, name="world"):
    print(f"Hello, {name}!")
    print(f"From: {', '.join(from_)}")

if __name__ == "__main__":
    arguably.run()
```

```console
user@machine:~$ python3 hello-4.py -h
usage: hello-4.py [-h] [--name NAME] [from ...]

positional arguments:
  from         (type: str)

options:
  -h, --help   show this help message and exit
  --name NAME  (type: str, default: world)
```
```console
user@machine:~$ python3 hello-4.py Graham John Terry Eric Terry Michael --name Python
Hello, Python!
From: Graham, John, Terry, Eric, Terry, Michael
```

To require at least one input to `*args`, use [`arguably.arg.required()`](../../api-reference/#arguably.arg.required).

## Adding help messages

To add help messages to parameters, add a docstring. It can be any of the major formats: reStructuredText (Sphinx),
Google, Numpydoc, or Epydoc. We'll use Google's style for this example.

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/hello-5.py">[source]</a>
</sub></div>

```python
@arguably.command
def hello(*from_, name="world"):
    """
    this will say hello to someone

    Args:
        from_: greetings are sent from these people
        name: is who this will greet
    """
    print(f"Hello, {name}!")
    print(f"From: {', '.join(from_)}")
```

```console
user@machine:~$ python3 hello-5.py -h
usage: hello-5.py [-h] [--name NAME] [from ...]

this will say hello to someone

positional arguments:
  from         greetings are sent from these people (type: str)

options:
  -h, --help   show this help message and exit
  --name NAME  is who this will greet (type: str, default: world)
```

### Option names

By default, any `--options` will have a long name which is a [normalized version](../subcommands/#name-normalization)
of their Python name. Options do not have a short name by default.

Option names can be controlled by prefixing their description with a value in square brackets `[]`:

* `[-t]` &rightarrow; `-t` is the short name
* `[--to]` &rightarrow; `--to` is the long name
* `[-t/--to]` &rightarrow; `-t` is the short name and `--to` is the long name
* `[-t/]` &rightarrow; `-t` is the short name, the long name is *removed*.

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/hello-6.py">[source]</a>
</sub></div>

```python
@arguably.command
def hello(*, from_="me", name="world"):
    """
    this will say hello to someone

    Args:
        from_: [-f/] the sender of these greetings
        name: [-t/--to] the receiver of these greetings
    """
    print(f"Hello, {name}!")
    print(f"From: {from_}")
```

```console
user@machine:~$ python3 etc/scripts/hello-6.py -h
usage: hello-6.py [-h] [-f FROM] [-t TO]

this will say hello to someone

options:
  -h, --help   show this help message and exit
  -f FROM      the sender of these greetings (type: str, default: me)
  -t, --to TO  the receiver of these greetings (type: str, default: world)
```

### Metavars

A metavar is what gets printed in the usage string to represent the user-provided value. More explanation for that
[here](https://docs.python.org/3/library/argparse.html#metavar).

By default, the metavar for any argument is the uppercase version of its name. To change the metavar, wrap any word in
its description in curly braces `{}`. Tuples can specify one value or a number of comma-separated values equal to the
tuple length.

* `{who}` &rightarrow; `WHO` is the metavar
* `{x,y,z}` &rightarrow; `X`, `Y`, and `Z` are the metavars for a tuple of length 3

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/hello-7.py">[source]</a>
</sub></div>

```python
@arguably.command
def hello(*, from_="me", name="world"):
    """
    this will say hello to someone

    Args:
        from_: [-f/] the {sender} of these greetings
        name: [-t/--to] the {receiver} of these greetings
    """
    print(f"Hello, {name}!")
    print(f"From: {from_}")
```

```console
user@machine:~$ python3 etc/scripts/hello-7.py -h
usage: hello-7.py [-h] [-f SENDER] [-t RECEIVER]

this will say hello to someone

options:
  -h, --help         show this help message and exit
  -f SENDER          the sender of these greetings (type: str, default: me)
  -t, --to RECEIVER  the receiver of these greetings (type: str, default: world)
```

Compare the last line with how it was before:

```console
Before:  -t, --to TO  the receiver of these greetings (type: str, default: world)
After:   -t, --to RECEIVER  the receiver of these greetings (type: str, default: world)
```

## Summary

`arguably` looks at all decorated functions and maps their arguments from Python to the CLI.

```python
@arguably.command
def some_function(required, not_required=2, *others: int, option: float = 3.14):
    ...
```

```console
user@machine:~$ ./intro.py -h
usage: intro.py [-h] [-x OPTION] required [not-required] [others ...]
...
```

| This Python ...                                | ... becomes this on the CLI.                   |
|------------------------------------------------|------------------------------------------------|
| positional args, no default `required`         | positional CLI args, required `required`       |
| positional args, with default `not_required=2` | positional CLI args, optional `[not-required]` |
| positional args, variadic `*others`            | any extra positional CLI args `[others ...]`   |
| keyword-only arguments `option`                | command-line options `[-x OPTION]`             |

Docstrings are used for command and argument help messages. They can also:

* Change option names:
    * Set the short name with `[-n]`
    * Change the long name with `[--name]`
    * Set the short and long names with `[-n/--name]`
    * Set the short name and remove the long name with `[-n/]`
* Change the metavar of an argument to `SOMETHING` by wrapping a word in curly braces: `{something}`
