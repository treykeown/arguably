import arguably

@arguably.command
def hello(name="world", *, shout=False):
    """
    says hello to someone
    Args:
        name: {who} to greet
        shout: will only use uppercase
    """
    message = f"Hello, {name}!"
    if shout:
        message = message.upper()
    print(message)

if __name__ == "__main__":
    arguably.run()
