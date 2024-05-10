import itertools
import json
import re
from typing import Any, Optional, Tuple, List

import nox


nox.options.sessions = ["test"]


@nox.session(python=["3.9", "3.10", "3.11", "3.12"])
def test(session: nox.Session) -> None:
    session.run("poetry", "install", external=True)
    session.run("ruff", "check", ".")
    session.run("mypy", "arguably/")
    session.run("pytest", "test", "--cov", "arguably", "--cov-report", "html", "--cov-report", "json")


########################################################################################################################
# For GitHub Actions
# Taken from https://stackoverflow.com/a/66747360


def _get_session_func(session: nox.Session) -> Any:
    """get the desired base session to generate the list for"""
    if len(session.posargs) != 1:
        raise ValueError("This session has a mandatory argument: <base_session_name>")
    return globals()[session.posargs[0]]


def _get_session_versions(session_func: Any) -> List[str]:
    """list all sessions for this base session"""
    try:
        session_func.parametrize
    except AttributeError:
        sessions_list = ["%s-%s" % (session_func.__name__, py) for py in session_func.python]
    else:
        sessions_list = [
            "%s-%s(%s)" % (session_func.__name__, py, param)
            for py, param in itertools.product(session_func.python, session_func.parametrize)
        ]

    return sessions_list


# 3.8 compat for str.removeprefix
def remove_prefix(input_string: str, prefix: str) -> str:
    if prefix and input_string.startswith(prefix):
        return input_string[len(prefix) :]
    return input_string


@nox.session(python=False)
def get_versions(session: nox.Session) -> None:
    """(mandatory arg: <base_session_name>) prints all sessions for <base_session_name> for Github Actions"""
    session_func = _get_session_func(session)
    print(json.dumps([x.partition("-")[2] for x in _get_session_versions(session_func)]))


@nox.session(python=False)
def get_latest_version(session: nox.Session) -> None:
    """(mandatory arg: <base_session_name>) prints the latest session for <base_session_name> for Github Actions"""
    session_func = _get_session_func(session)
    cpython_matcher = re.compile(r"[0-9.]+")
    latest: Optional[Tuple[int, ...]] = None
    versions = _get_session_versions(session_func)
    prefix: str = "".join(next(iter(versions)).partition("-")[0:2])
    for version in versions:
        version = remove_prefix(version, prefix)
        if cpython_matcher.match(version):
            version_tuple = tuple(int(x) for x in version.split("."))
            if latest is None or version_tuple > latest:
                latest = version_tuple
    assert latest is not None
    print(json.dumps(".".join(str(x) for x in latest)))
