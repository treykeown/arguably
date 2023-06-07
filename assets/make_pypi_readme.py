#!/usr/bin/env python3
"""
Converts our README.md to a PyPI-compatible version... needed because PyPI does not yet support <picture>, see:
https://github.com/pypi/warehouse/issues/11251
"""


from pathlib import Path

project_path = Path(__file__).resolve().parent.parent
readme_src = project_path / "README.md"
readme_dst = project_path / "assets" / "PYPI_README.md"

# A bit hacky, but works for now.
with readme_src.open("r") as src:
    with readme_dst.open("w") as dst:
        for line in src.readlines():
            stripped_line = line.lstrip(" ")
            if (
                stripped_line.startswith("<picture")
                or stripped_line.startswith("</picture")
                or stripped_line.startswith("<source")
            ):
                continue
            dst.write(line)
