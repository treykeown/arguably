#!/usr/bin/env python3
"""this docstring is the description for the script"""

import arguably
import builtins

@arguably.command
def hey_there(first_name, last_name: str | None = None):
    """
    this will say hello to someone

    arguments without annotations (`first_name`) default to `str`
        ... unless the type can be inferred from their default value
    any union with `None` is removed, so `last_name` is parsed as `str`

    Args:
        first_name: the {first} name of the person to greet
        last_name: their {last} name
    """
    if last_name is None:
        full_name = first_name
    else:
        full_name = f"{first_name} {last_name}"
    print(f"Hello, {full_name}!")

@arguably.command(alias="g")
def good(*, shout=False):
    """
    this is a command with two subcommands

    everything after the `*` appears as an `--option`
    `shout` is inferred to be a `bool` because of its default value
        `bool` `--option`s take no value by design

    Args:
        shout: [-s] will shout out the greeting
    """
    if shout:
        # All prints are now UPPERCASE
        global print
        print = lambda msg: builtins.print(msg.upper())

@arguably.command
def good__morning(name):
    """Greet someone early in the day"""
    print(f"Good morning, {name}!")

@arguably.command
def good__night(name):
    """Say goodbye at night"""
    print(f"Good night, {name}!")

if __name__ == "__main__":
    # Parses the CLI arguments and calls the decorated functions
    arguably.run()
