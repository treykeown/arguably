import logging

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
