#!/usr/bin/env python3
"""
Build script for the docs. Contains a few workarounds for issues encountered with `mkdocs`.

From `docs/contributing.md`:

I ran into an issue where all the functions which were aliases of class methods weren't appearing in the automatically
generated docs. Snippet is below, link to source is here:
https://github.com/treykeown/arguably/blob/9c3655480aaa2bdd714db209de4ed7b74f8f1fd5/arguably/_context.py#L784-L786

```python
run = context.run
is_target = context.is_target
error = context.error
```

So I wrote a script, `mkdocs.py`. It temporarily swaps out the real `__init__.py` for a generated one which consists
solely of skeletons of the functions and classes exposed in `__all__`. No code is in the generated file, only signatures
and docstrings. The script also does a few other things:

* Strips the docstring from `__init__.py`
* Copies in images from `etc/logo`
* Tweaks `README.md` so that the light and dark mode images work
"""

import inspect
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Tuple, Iterator, List

# Annotated is 3.9 and up
if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

import arguably

project_root = Path(__file__).parent
module_root = project_root / "arguably"

logos = ["arguably_black.png", "arguably_white.png", "arguably_small.png", "arguably_tiny.png"]


@contextmanager
def swap_file(real: Path, real_tmp: Path) -> Iterator:
    """Temporarily swaps a file to another location"""
    shutil.move(str(real), str(real_tmp))
    try:
        yield
    finally:
        fake = real  # The fake file is currently at the real path
        shutil.copy(str(fake), str(fake.parent / f".fake.{fake.name}"))
        shutil.move(str(real_tmp), str(real))  # Restore real file


def get_members(obj: Any) -> List[Any]:
    """Get members of a class or module"""
    return [v for k, v in vars(obj).items() if not k.startswith("_") and not type(v).__name__.startswith("_")]


def get_signature(obj: Any) -> inspect.Signature:
    """Get the signature of a function or class"""
    try:
        return inspect.signature(obj)
    except ValueError:
        for ancestor in obj.__mro__:
            try:
                return inspect.signature(ancestor)
            except ValueError:
                pass
    raise Exception(f"Unable to find signature for {obj}")


def get_bases(cls: type) -> Tuple[type, ...]:
    """Get the classes this one inherits from, excluding any redundant ones."""
    classtree = inspect.getclasstree(list(inspect.getmro(cls)))
    real_bases: Tuple[type, ...] = tuple()
    stack = [classtree]
    while len(stack) > 0:
        curr = stack.pop()
        to_visit = list()
        for item in curr:
            if isinstance(item, tuple) and item[0] == cls:
                real_bases = item[1]
                break
            elif isinstance(item, list):
                to_visit.append(item)
        else:
            stack.extend(to_visit)
    return real_bases


def produce_file(path: Path) -> None:
    """Make the fake __init__.py"""
    with path.open("w") as fh:
        # good_doc_lines = "\n\n".join(arguably.__doc__.split("\n\n")[1:-1])
        # fh.write(f'"""\n{good_doc_lines}\n"""\n')
        # fh.write("\n")
        fh.write("import enum\n")
        fh.write("from typing import *\n")
        fh.write("from abc import ABC\n")
        fh.write("\n")

        members = get_members(arguably)
        for member in sorted(members, key=lambda x: arguably.__all__.index(x.__name__)):
            signature_str = str(get_signature(member))
            if isinstance(member, type):
                signature_str = "(self, " + signature_str[1:]
                real_bases = get_bases(member)
                fh.write(f"class {member.__name__}({', '.join(b.__name__ for b in real_bases)}):\n")
                if member.__doc__ is not None:
                    fh.write(f'    """{member.__doc__}"""\n')
                fh.write(f"    def __init__{signature_str}:\n")
                fh.write("        pass\n")
                fh.write("\n")
                for cls_member in get_members(member):
                    signature = get_signature(cls_member)
                    if callable(cls_member):
                        static_cls_member = inspect.getattr_static(member, cls_member.__name__)
                        if isinstance(static_cls_member, classmethod):
                            fh.write("    @classmethod\n")
                        elif isinstance(static_cls_member, staticmethod):
                            fh.write("    @staticmethod\n")
                        fh.write(f"    def {cls_member.__name__}{signature}:\n")
                        fh.write(f'        """{cls_member.__doc__}"""\n')
                        fh.write("\n")
                    else:
                        raise Exception(f"Unsupported member type {type(cls_member)} for {cls_member} in {member}")
            else:
                assert callable(member)
                fh.write(f"def {member.__name__}{signature_str}:\n")
                fh.write(f'    """{member.__doc__}"""\n')
            fh.write("\n")


def run_mkdocs(target: str) -> None:
    args = ["mkdocs", target]
    print(f"running: {' '.join(args)}")
    print()
    subprocess.run(args)


def copy_logos() -> None:
    os.makedirs(project_root / "docs" / "images", exist_ok=True)
    for logo in logos:
        shutil.copy(project_root / "etc" / "logo" / logo, project_root / "docs" / "images" / logo)


def copy_readme() -> None:
    """Copy the README to use as the index page, but fix the dark/light mode images"""
    readme = project_root / "README.md"
    index = project_root / "docs" / "index.md"
    with readme.open("r") as src:
        with index.open("w") as dst:
            in_picture = False
            dst.write("![arguably logo](images/arguably_black.png#only-light)\n")
            dst.write("![arguably logo](images/arguably_white.png#only-dark)\n")
            for line in src.readlines():
                stripped_line = line.lstrip(" ")
                if stripped_line.startswith("<picture"):
                    in_picture = True
                    continue
                if stripped_line.startswith("</picture"):
                    in_picture = False
                    continue
                if in_picture:
                    continue
                dst.write(line)


@arguably.command
def main(mkdocs_cmd: Annotated[str, arguably.arg.choices("build", "serve")]) -> None:
    """
    due to issues running mkdocs directly on our module, we stub out a fake one and run mkdocs on that

    Args:
        mkdocs_cmd: the command that will be passed to mkdocs
    """
    os.chdir(project_root)
    copy_logos()
    copy_readme()
    with swap_file(module_root / "__init__.py", module_root / ".real.__init__.py"):
        produce_file(module_root / "__init__.py")
        run_mkdocs(mkdocs_cmd)


if __name__ == "__main__":
    arguably.run()
