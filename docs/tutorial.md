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

More coming soon.
