import arguably

@arguably.command
def hello(*from_, name="world"):
    print(f"Hello, {name}!")
    print(f"From: {', '.join(from_)}")

if __name__ == "__main__":
    arguably.run()
