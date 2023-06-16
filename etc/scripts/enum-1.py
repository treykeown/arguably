import arguably
import enum

class Direction(enum.Enum):
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

@arguably.command
def move(start: tuple[int, int], direction: Direction):
    x, y = start
    dx, dy = direction.value
    end = (x + dx, y + dy)
    print(f"{start=}", f"{direction}", f"{end=}")

if __name__ == "__main__":
    arguably.run()
