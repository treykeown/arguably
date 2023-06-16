# API Reference

## Overview

### Need-to-know

In short, only two functions are required to use `arguably`:

* [`@arguably.command`](#arguably.command) to mark which functions to put on the CLI
* [`arguably.run()`](#arguably.run) parses the CLI arguments and calls the marked functions

### Extras

The rest of the functions aren't necessary except in specific use cases:

* [`arguably.error()`](#arguably.error) lets you error out if an input is the correct type but isn't acceptable
* [`arguably.is_target()`](#arguably.is_target) tells you if the targeted command is being run, or if one of its
ancestors is being run
* [`@arguably.subtype`](#arguably.subtype) marks a class as being a subclass buildable through `arguably.arg.builder()`

### Special behaviors

There are a number of special behaviors you can attach to a parameter:

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

### Exceptions

Additionally, there are two exceptions:

* [`arguably.ArguablyException`](#arguably.ArguablyException) raised if you messed up when setting up `arguably`
* [`arguably.ArguablyWarning`](#arguably.ArguablyWarning) passed to `warnings.warn()` if you messed up when setting up
`arguably`, but not badly. Also used if `python3 -m arguably <script.py>` is used, but there were some problems running
the script.

## Details

::: arguably
