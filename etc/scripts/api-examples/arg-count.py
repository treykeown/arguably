import arguably
from typing import Annotated

@arguably.command
def process(
    *,
    verbose: Annotated[int, arguably.arg.count()],
):
    """
    :param verbose: [-v] verbosity
    """
    print(f"{verbose=}")

if __name__ == "__main__":
    arguably.run()
