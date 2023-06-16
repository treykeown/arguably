import arguably

@arguably.command
def hello(*, name="world"):
    """
    this will say hello to someone

    Args:
        name: is who this will greet
    """
    print(f"Hello, {name}!")

if __name__ == "__main__":
    arguably.run()
