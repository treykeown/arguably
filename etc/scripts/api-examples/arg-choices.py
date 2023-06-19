import arguably
from typing import Annotated

@arguably.command
def move(
    direction: Annotated[str, arguably.arg.choices("left", "right", "up", "down")]
):
    """An enum is usually recommended for cases like this"""
    print(f"{direction=}")

if __name__ == "__main__":
    arguably.run()
