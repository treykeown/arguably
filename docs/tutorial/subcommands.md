# Subcommands

## Introduction

Marking multiple functions with `@arguably.command` will make them show up as subcommands on the CLI:

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/goodbye-1.py">[source]</a>
</sub></div>

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
```
```console
user@machine:~$ python3 goodbye-1.py hello Python
Hello, Python!
```
```console
user@machine:~$ python3 goodbye-1.py goodbye Python
Goodbye, Python!
```

### Name normalization

Single underscores `_` in a function name are converted to a dash `-`. Also, any leading or trailing underscores are
stripped.

* `def foo_bar():` &rightarrow; `foo-bar`
* `def list_():` &rightarrow; `list`
* `def _asdf():` &rightarrow; `asdf`
* `def __foo__():` &rightarrow; `foo`
* `def ___really_really_long_name():` &rightarrow; `really-really-long-name`

## Multi-level subcommands

To add a subcommand to a parent command, separate their names with two underscores `__`. For example:

* `s3__ls` &rightarrow; `s3 ls`
* `ec2__start_instances` &rightarrow; `ec2 start-instances`

Continuing this example:

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/aws-1.py">[source]</a>
</sub></div>

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
```
```console
user@machine:~$ python3 aws-1.py s3 -h
usage: aws-1.py s3 [-h] command ...

positional arguments:
  command
    ls        list objects
    cp        copy objects

options:
  -h, --help  show this help message and exit
```
```console
user@machine:~$ python3 aws-1.py s3 ls -h
usage: aws-1.py s3 ls [-h] [path]

list objects

positional arguments:
  path        path to list under (type: str, default: /)

options:
  -h, --help  show this help message and exit
```
```console
user@machine:~$ python3 aws-1.py s3 ls /foo/bar
Listing objects under /foo/bar
```

### Hierarchy

You may have noticed that `ec2` and `s3` had no description. This is because they are automatically created stubs. We
can define them ourselves and attach arguments to them:

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/aws-2.py">[source]</a>
</sub></div>

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
```
```console
user@machine:~$ python3 aws-2.py s3 --bucket mybucket ls
Using bucket: mybucket
Listing objects under /
```

As you can see, `def s3(*, bucket)` was called first and printed the bucket name to use. After that,
`def s3__ls(path="/")` was invoked. This is because all ancestors are invoked before the target command is invoked. For
a more complex example:

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/nested-1.py">[source]</a>
</sub></div>

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

## The `__root__` function

If a function named `__root__` is marked with `@arguably.command`, it always appears as the highest ancestor for
commands in the script. This allows global options and actions to be placed at the root of the script.

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/root-1.py">[source]</a>
</sub></div>

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

## Checking `arguably.is_target()`

Sometimes you'll want to allow a command in the heirarchy to process its input arguments, but bail if it wasn't the
target. For that, you can use `arguably.is_target()`. This returns `False` if the currently-executing function was
called as an ancestor of the target command, and `True` every other time.

<div align="right" class="code-source"><sub>
    <a href="https://github.com/treykeown/arguably/blob/main/etc/scripts/root-2.py">[source]</a>
</sub></div>

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
```
```console
user@machine:~$ python3 root-2.py --config-file foo.yml hi
Using config foo.yml
hi is the target!
```
