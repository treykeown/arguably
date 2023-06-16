import arguably


@arguably.command
def hello(name):
    print(f"Hello, {name}!")


if __name__ == "__main__":
    arguably.run()
