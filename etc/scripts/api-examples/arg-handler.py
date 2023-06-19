import arguably
from typing import Annotated

@arguably.command
def handle_it(
    version: Annotated[int, arguably.arg.handler(lambda s: int(s.split("-")[-1]))] = None
):
    print(f"{version=}")

if __name__ == "__main__":
    arguably.run()
