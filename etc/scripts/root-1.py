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
