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
