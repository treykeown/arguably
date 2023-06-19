import arguably
from typing import Annotated

@arguably.command
def email(
    from_: str,
    *to: Annotated[str, arguably.arg.required()]
):
    print(f"{from_=}", f"{to=}")

if __name__ == "__main__":
    arguably.run()
