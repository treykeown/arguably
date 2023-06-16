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
user@machine:~$ python3 process.py -h
usage: process.py [-h] [FILE ...]

process many files

positional arguments:
  FILE        the files to process (type: str)

options:
  -h, --help  show this help message and exit

user@machine:~$ python3 process.py report-1.csv report-2.csv report-3.csv
Processing report-1.csv...
Processing report-2.csv...
Processing report-3.csv...
```
