import arguably
from dataclasses import dataclass
from typing import Annotated

class Nic: ...

@arguably.subtype(alias="tap")
@dataclass
class TapNic(Nic):
    model: str

@arguably.subtype(alias="user")
@dataclass
class UserNic(Nic):
    hostfwd: str

@arguably.command
def qemu_style(*, nic: Annotated[list[Nic], arguably.arg.builder()]):
    print(f"{nic=}")

if __name__ == "__main__":
    arguably.run()
