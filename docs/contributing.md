# Contributing

## Prerequisites

`poetry` is used for managing this project. To install poetry, follow
[this guide](https://python-poetry.org/docs/#installation).

## Setup

1. Clone the repository - `git clone git@github.com:treykeown/arguably.git`
2. Set up the project - `poetry install`
3. Activate the project virtualenv - `source .venv/bin/activate`
4. Install the pre-commit hooks - `pre-commit install`

That's it! You should be ready to make a change and [open a pull request](https://github.com/treykeown/arguably/pulls).
Just remember to run `pytest` as you're developing to make sure everything works.

I can help debug if you're having issues, just [open a discussion](https://github.com/treykeown/arguably/discussions).

It's not necessary, but if you're using `pyenv`, you can install all the supported Python versions to make sure all
tests pass before submitting your pull request. See the [Testing section](#testing) below.

## Pre-commit Hooks

If this is your first time using pre-commit hooks, all you need to know is that when you run `git commit`, a lot of
tools are invoked to check the code. Notably absent is `pytest` - tests take quite a bit of time to run, and
[commiting should be fast](https://github.com/pre-commit/pre-commit-hooks/issues/291#issuecomment-394167917). You'll
need to make sure to run the tests yourself.

If a pre-commit hook fails, it's because it just reformatted something (except for `mypy`, which will just complain and
not fix itself). If something fails, you can just `git add` and `git commit` again with the same message. This will
include the changes the pre-commit hook made to automatically reformat your code.

## Other Details

### Code Style

As with many projects, `black` is used to automatically format code. Its output is not always as clear as
hand-formatting everything, but it's much faster and works well for projects with many contributors. You will not have
to manually invoke `black`, it runs during the pre-commit hooks.

If you do not type hint your functions, `mypy` will fail. Please add docstrings, but no need to document parameters
(unless you want to!). A short description of each class or function is great.

Sparse comments are appreciated!

### Linting

`ruff` and `mypy` are used for checking code correctness. These are automatically run as a part of the pre-commit hooks.
If you want to invoke them manually, from the project root directory:

* `ruff .`
* `mypy arguably/`

### Testing

Originally, tests were only conducted through directly running `pytest`. Now, in order to support multiple Python
versions, `nox` is used to automatically test Python 3.8 through 3.11. Running all the tests for all versions takes a
bit of time, so during normal development I directly run `pytest` and only run `nox` at the very end, before pushing. To
invoke each, from the project root directory:

* `pytest test --cov arguably --cov-report html` (will put a coverage report in the `htmlcov/` directory)
* `nox` (automatically runs `noxfile.py`)

`nox` will require extra setup. You'll need to install Python versions 3.8 through 3.11 using `pyenv`:

* `pyenv install 3.11 3.10 3.9 3.8`
* `pyenv global 3.11 3.10 3.9 3.8`

### Building Docs

I've been fighting `mkdocs`. I'm not sure that I'm winning.

I ran into an issue where all the functions which were aliases of class methods weren't appearing in the automatically
generated docs. Snippet is below, link to source is [here](https://github.com/treykeown/arguably/blob/9c3655480aaa2bdd714db209de4ed7b74f8f1fd5/arguably/_context.py#L784-L786).

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

I'm hoping to work on a proper `mkdocs` plugin one day to allow these sorts of tweaks without the steps I've taken here.

If you can save me from my own madness here, please help me.

#### TL;DR

Run `./mkdocs.py serve` to check the docs. `arguably` will not be usable as long as this is running, since I do some
magic to work around a few `mkdocs` issues. Don't try to make a commit while `./mkdocs.py serve` is running.

### Making Releases

I need to manually add a tag on GitHub for the new version, and it'll be automatically published on PyPI. At some point
in the future, we'll have a changelog to go along with this.
