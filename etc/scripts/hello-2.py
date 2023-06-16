import arguably


@arguably.command
def hello(name="world"):
    print(f"Hello, {name}!")


if __name__ == "__main__":
    arguably.run()
