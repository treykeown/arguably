#!/usr/bin/env python3

import arguably


@arguably.command
def some_function(required, not_required=2, *others: int, option: float = 3.14):
    """
    this function is on the command line!

    Args:
        required: a required parameter
        not_required: this one isn't required, since it has a default
        *others: all the other positional arguments go here
        option: [-x] an option, short name is in brackets
    """
    ...


if __name__ == "__main__":
    arguably.run()
