import itertools
import json

import nox


@nox.session(python=False)
def gha_list(session: nox.Session) -> None:
    """(mandatory arg: <base_session_name>) Prints all sessions available for <base_session_name>, for GithubActions."""

    # get the desired base session to generate the list for
    if len(session.posargs) != 1:
        raise ValueError("This session has a mandatory argument: <base_session_name>")
    session_func = globals()[session.posargs[0]]

    # list all sessions for this base session
    try:
        session_func.parametrize
    except AttributeError:
        sessions_list = ["%s-%s" % (session_func.__name__, py) for py in session_func.python]
    else:
        sessions_list = [
            "%s-%s(%s)" % (session_func.__name__, py, param)
            for py, param in itertools.product(session_func.python, session_func.parametrize)
        ]

    # print the list so that it can be caught by GHA.
    # Note that json.dumps is optional since this is a list of string.
    # However it is to remind us that GHA expects a well-formatted json list of strings.
    print(json.dumps(sessions_list))


@nox.session(python=["3.8", "3.9", "3.10", "3.11"])
def test(session: nox.Session) -> None:
    session.run("poetry", "install", external=True)

    session.run("pytest", "test", "--cov", "arguably", "--cov-report", "html", "--cov-report", "json")


nox.options.sessions = ["test"]
