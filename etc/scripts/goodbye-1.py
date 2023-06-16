import arguably

@arguably.command
def hello(name):
    """this will say hello to someone"""
    print(f"Hello, {name}!")

@arguably.command
def goodbye(name):
    """this will say goodbye to someone"""
    print(f"Goodbye, {name}!")

if __name__ == "__main__":
    arguably.run()
