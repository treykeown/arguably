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
def hello(*, name="world"):
    """
    this will say hello to someone

    Args:
        name: is who this will greet
    """
    print(f"Hello, {name}!")
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

### Short names and metavars

There are two special things you can put in your docstring that `arguably` will use.

| Format          | Applies to...   | Function                     |
|-----------------|-----------------|------------------------------|
| `[-n] ...`      | `--option` only | Short name for an `--option` |
| `... {WHO} ...` | any argument    | Metavar for an argument      |

A metavar is what gets printed in the usage string to represent the user-provided value. More explanation for that
[here](https://docs.python.org/3/library/argparse.html#metavar).

An example of using these directives to alias `--name` to `-n`, and to make its metavar `who`:

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/hello-6.py">[source]</a>
</sub></div>

```python
@arguably.command
def hello(*from_, name="world"):
    """
    this will say hello to someone

    Args:
        from_: greetings are sent from these people
        name: [-n] is {who} this will greet
    """
    print(f"Hello, {name}!")
    print(f"From: {', '.join(from_)}")
```

```console
user@machine:~$ python3 hello-6.py -h
usage: hello-6.py [-h] [-n WHO] [from ...]

this will say hello to someone

positional arguments:
  from            greetings are sent from these people (type: str)

options:
  -h, --help      show this help message and exit
  -n, --name WHO  is who this will greet (type: str, default: world)
```

Compare the last line with how it was before:

```console
Before:  --name NAME     is who this will greet (type: str, default: world)
After:   -n, --name WHO  is who this will greet (type: str, default: world)
```
