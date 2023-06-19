#!/usr/bin/env python3
import arguably

@arguably.command(alias="f")
def first(): ...

@arguably.command(alias="s")
def second(): ...

@arguably.command
def second__subcmd1(): ...

def second__subcmd2(): ...
arguably.command(second__subcmd2)  # Can also be invoked this way

if __name__ == "__main__":
    arguably.run()
