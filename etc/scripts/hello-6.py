import arguably

@arguably.command
def hello(*, from_="me", name="world"):
    """
    this will say hello to someone

    Args:
        from_: [-f/] the sender of these greetings
        name: [-t/--to] the receiver of these greetings
    """
    print(f"Hello, {name}!")
    print(f"From: {from_}")

if __name__ == "__main__":
    arguably.run()
