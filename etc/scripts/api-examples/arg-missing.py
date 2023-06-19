import arguably
from pathlib import Path
from typing import Annotated

@arguably.command
def do_something(
    *,
    log: Annotated[Path | None, arguably.arg.missing("~/.log.txt")] = None
):
    print(f"{log=}")

if __name__ == "__main__":
    arguably.run()
