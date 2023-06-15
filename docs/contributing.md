# Contributing

## Prerequisites

`poetry` is used for managing this project. To install poetry, follow
[this guide](https://python-poetry.org/docs/#installation).

## Setup

1. Clone the repository - `user@machine:~$ git clone git@github.com:treykeown/arguably.git`
2. Set up the project - `poetry install`
3. Activate the project virtualenv - `source .venv/bin/activate`
4. Install the pre-commit hooks - `pre-commit install`

## Linting

`ruff` and `mypy` are used for checking code correctness. These are automatically run as a part of the pre-commit hooks.
If you want to invoke them manually, from the project root directory:

* `ruff .`
* `mypy arguably/`

## Testing

Originally, tests were only conducted through directly running `pytest`. Now, in order to support multiple Python
versions, `nox` is used to automatically test Python 3.8 through 3.11. Running all the tests for all versions takes a
bit of time, so during normal development I directly run `pytest` and only run `nox` at the very end, before pushing. To
invoke each, from the project root directory:

* `pytest test --cov arguably --cov-report html` (will put a coverage report in the `htmlcov/` directory)
* `nox` (automatically runs `noxfile.py`)

## Code Style

As with many projects, `black` is used to automatically format code. Its output is not always as clear as
hand-formatting everything, but it's much faster and works well for projects with many contributors. You will not have
to manually invoke `black`, it runs during the pre-commit hooks.

If you do not type hint your functions, `mypy` will fail. Please add docstrings, but no need to document parameters
(unless you want to!). A short description of each class or function is great.

Sparse comments are appreciated!

## Pre-commit Hooks

If this is your first time using pre-commit hooks, all you need to know is that when you run `git commit`, a lot of
tools are invoked to check the code. Notably absent is `pytest` - tests take quite a bit of time to run, and
[commiting should be fast](https://github.com/pre-commit/pre-commit-hooks/issues/291#issuecomment-394167917). You'll
need to make sure to run the tests yourself.

If a pre-commit hook fails, it's because it just reformatted something (except for `mypy`, which will just complain and
not fix itself). If something fails, you can just `git add` and `git commit` again with the same message. This will
include the changes the pre-commit hook made to automatically reformat your code.
