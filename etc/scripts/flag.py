import arguably
import enum
from pathlib import Path

class Permissions(enum.Flag):
    """
    Permission flags

    Attributes:
        READ: [-r] allows for reads
        WRITE: [-w] allows for writes
        EXECUTE: [-x] allows for execution
    """

    READ = 4
    WRITE = 2
    EXECUTE = 1

class PermissionsAlt(enum.Flag):
    """Annotations can also appear like this"""

    READ = 4
    """[-r] allows for reads"""
    WRITE = 2
    """[-w] allows for writes"""
    EXECUTE = 1
    """[-x] allows for execution"""

@arguably.command
def chmod(file: Path, *, flags: Permissions = Permissions(0)):
    """
    change file permissions

    Args:
        file: the file to modify
        flags: permission flags
    """
    print(f"{file=}", f"{flags=}")

if __name__ == "__main__":
    arguably.run()
