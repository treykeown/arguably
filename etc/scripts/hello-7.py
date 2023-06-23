import arguably

@arguably.command
def hello(*from_, name="world"):
    """
    this will say hello to someone

    Args:
        from_: greetings are sent from these people
        name: [-t/--to] is {who} this will greet
    """
    print(f"Hello, {name}!")
    print(f"From: {', '.join(from_)}")

if __name__ == "__main__":
    arguably.run()
