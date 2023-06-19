#!/usr/bin/env python3
"""description for this script"""
from io import StringIO

import arguably

__version__ = "1.2.3"

@arguably.command
def example(): ...

if __name__ == "__main__":
    output = StringIO()
    try:
        arguably.run(
            name="myname",
            always_subcommand=True,
            version_flag=True,
            command_metavar="mycmd",
            output=output
        )
    finally:
        print(f"Captured output length: {len(output.getvalue())=}")
        print()
        print(output.getvalue(), end="")
