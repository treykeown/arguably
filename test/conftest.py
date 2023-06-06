import abc
import dataclasses
import io
import sys
from io import StringIO
from pathlib import Path
from typing import Generator, Callable, Annotated, cast, Optional

import pytest

import noarg
from . import MANUAL, Permissions, PermissionsAlt, HiBye


########################################################################################################################
# instrumentation


@pytest.fixture(autouse=True)
def noarg_context(request) -> Generator:
    # wipe noarg without creating a new instance
    noarg._context.__dict__.clear()
    noarg._context.__init__()

    # wipe sys.argv
    sys.argv.clear()
    sys.argv.append(request.function.__name__)

    yield


@pytest.fixture
def iobuf() -> StringIO:
    return io.StringIO()


########################################################################################################################
# basic


@pytest.fixture
def fn_basic(iobuf: StringIO) -> Callable:
    @noarg.command
    def basic():
        iobuf.write("basic\n")

    return basic


########################################################################################################################
# hello


@pytest.fixture
def fn_hello(iobuf: StringIO) -> Callable:
    @noarg.command
    def hello(name, age=30, *, howdy=False, lastname=None) -> None:
        """
        says hello to you
        :param name: your name
        :param age: your age
        :param howdy: [-H] say howdy instead of hello
        :param lastname: [-l] your {SURNAME}
        """
        greeting = "Howdy" if howdy else "Hello"
        if lastname is None:
            lastname = ""
        iobuf.write(f"{greeting}, {name} {lastname}! You'll be {age + 1} next year.\n")

    return hello


########################################################################################################################
# enum


@pytest.fixture
def fn_chmod(iobuf: StringIO) -> Callable:
    @noarg.command
    def chmod(
        file: Path,
        *,
        flags: Permissions = Permissions(0),
    ):
        iobuf.write(f"{file}: ")
        if flags & Permissions.READ:
            iobuf.write("r")
        if flags & Permissions.WRITE:
            iobuf.write("w")
        if flags & Permissions.EXECUTE:
            iobuf.write("x")
        iobuf.write("\n")

    return chmod


@pytest.fixture
def fn_chmod_alt(iobuf: StringIO) -> Callable:
    @noarg.command
    def chmod_alt(
        file: Path,
        *,
        flags: PermissionsAlt = PermissionsAlt(0),
    ):
        iobuf.write(f"{file}: ")
        if flags & PermissionsAlt.READ:
            iobuf.write("r")
        if flags & PermissionsAlt.WRITE:
            iobuf.write("w")
        if flags & PermissionsAlt.EXECUTE:
            iobuf.write("x")
        iobuf.write("\n")

    return chmod_alt


@pytest.fixture
def fn_say(iobuf: StringIO) -> Callable:
    @noarg.command
    def say(which: HiBye) -> None:
        """
        say hi or bye
        :param which: which to say
        """
        iobuf.write(f"{which.value}")

    return say


@pytest.fixture
def fn_say_annotated_enum(iobuf: StringIO) -> Callable:
    @noarg.command
    def say_enum(which: Annotated[HiBye, noarg.arg.choices(HiBye.HI, HiBye.BYE)]) -> None:
        """
        say hi or bye
        :param which: which to say
        """
        iobuf.write(f"which: {which.value}\n")

    return say_enum


########################################################################################################################
# advanced


@pytest.fixture
def scope_advanced(iobuf: StringIO) -> dict[str, Callable]:
    @noarg.command
    def __root__(*, loud: bool = False):
        """
        advanced test
        :param loud: make it loud
        """
        if not MANUAL:
            assert not noarg.is_target()
        iobuf.write("> root\n")

        if loud:
            iobuf.write("__root__ loud\n")

    @noarg.command
    def add(*numbers: Annotated[int, noarg.arg.required()], coords: Optional[tuple[int, int, int]] = None) -> None:
        """
        adds a bunch of numbers together
        :param numbers: the numbers {NUMS} to add
        :param coords: [-c] coordinates {X,Y,Z} updated with the sum
        """
        if not MANUAL:
            assert noarg.is_target()
        iobuf.write("> add\n")

        total = sum(numbers)
        iobuf.write(f"add sum: {total}\n")
        if coords is not None:
            iobuf.write(f"add coords: {coords[0]+total}, {coords[1]+total}, {coords[2]+total}\n")

    @noarg.command
    def give(
        *,
        slowly: bool = False,
    ) -> None:
        """
        give something
        :param slowly: give it slowly
        """
        iobuf.write("> give\n")
        if slowly:
            iobuf.write("give slowly\n")
        if noarg.is_target():
            iobuf.write("give is main\n")

    @noarg.command(alias="a")
    def give__ascii() -> None:
        """gives ascii"""
        if not MANUAL:
            assert noarg.is_target()
        iobuf.write("> give ascii\n")

    @noarg.command
    def give__zen(
        *,
        rotten: bool = False,
    ) -> None:
        """
        gives zen
        :param rotten: makes the zen rotten
        """
        if not MANUAL:
            assert noarg.is_target()
        iobuf.write("> give zen\n")

        if rotten:
            iobuf.write("give zen rotten\n")

    @noarg.command
    def do__a_dance() -> None:
        """
        does a dance
        """
        if not MANUAL:
            assert noarg.is_target()
        iobuf.write("> do a-dance\n")

    @noarg.command(alias="h")
    def hey_you(
        name: str,
    ) -> None:
        """
        says hello to you
        :param name: your name
        """
        if not MANUAL:
            assert noarg.is_target()
        iobuf.write("> hey-you\n")
        iobuf.write(f"hey-you name: {name}")

    return cast(dict[str, Callable], {k: v for k, v in locals().items() if k != "iobuf"})


########################################################################################################################
# annotated


@pytest.fixture
def scope_annotated(iobuf: StringIO) -> dict[str, Callable]:
    class Logger(abc.ABC):
        @abc.abstractmethod
        def log(self, message: str) -> None:
            """log somewhere"""

        def __repr__(self):
            return f"{self.__class__.__name__}()"

    @noarg.subtype(alias="none")
    class NoLogger(Logger):
        """will not log"""

        def log(self, message: str) -> None:
            iobuf.write(f"~none: {message}\n")

    @noarg.subtype(alias="term")
    class TerminalLogger(Logger):
        """terminal logger"""

        def log(self, message: str) -> None:
            iobuf.write(f"~term: {message}\n")

    class FileLogger(Logger):
        def __init__(self, path: Path):
            """
            file logger
            :param path: path to log file
            """
            self._path = path.expanduser()

        def log(self, message: str) -> None:
            iobuf.write(f"~file {self._path}: {message}\n")

        def __repr__(self):
            return f"{self.__class__.__name__}(path={self._path})"

    noarg.subtype(FileLogger, alias="file")

    @dataclasses.dataclass
    class Complex:
        foo: int
        bar: str

    @noarg.command
    def log(message: str = "Howdy, there!", *, logger: Annotated[Logger, noarg.arg.builder()] = NoLogger()) -> None:
        """
        logs a hello
        :param message: message to log
        :param logger: what to use for logging
        """
        logger.log(message)

    @noarg.command
    def dataclass(dc: Annotated[Complex, noarg.arg.builder()]) -> None:
        """
        build a dataclass
        :param dc: spec for dataclass
        """
        iobuf.write(f"dataclass: {dc}\n")

    @noarg.command
    def explain(*, verbose: Annotated[int, noarg.arg.count()] = 0):
        """
        explain something
        :param verbose: [-v] be verbose
        """
        iobuf.write(f"verbosity: {verbose}\n")

    @noarg.command
    def high_five(*people: Annotated[str, noarg.arg.required()]):
        """
        high-fives people
        :param people: who to high-five
        """
        iobuf.write(f"people: {','.join(people)}\n")

    @noarg.command
    def email_alt(
        from_: str,
        cc: list[str],
        *to: str,
        bcc: Optional[list[str]] = None,
    ):
        """
        emails people
        :param from_: email address to send from
        :param cc: email addresses to cc to
        :param to: email addresses to send to
        :param bcc: email addresses to bcc to
        """
        if bcc is None:
            iobuf.write("bcc is none")
            bcc = list()

        iobuf.write(f"from: {from_}\n")
        for to_address in to:
            iobuf.write(f"to: {to_address}\n")
        for cc_address in cc:
            iobuf.write(f"cc: {cc_address}\n")
        for bcc_address in bcc:
            iobuf.write(f"bcc: {bcc_address}\n")

    @noarg.command
    def email(
        from_: str,
        *to: Annotated[str, noarg.arg.required()],
        cc: list[str],
        bcc: Optional[list[str]] = None,
    ):
        """
        emails people
        :param from_: email address to send from
        :param to: email addresses to send to
        :param cc: email addresses to cc to
        :param bcc: email addresses to bcc to
        """
        if bcc is None:
            iobuf.write("bcc is none")
            bcc = list()

        iobuf.write(f"from: {from_}\n")
        for to_address in to:
            iobuf.write(f"to: {to_address}\n")
        for cc_address in cc:
            iobuf.write(f"cc: {cc_address}\n")
        for bcc_address in bcc:
            iobuf.write(f"bcc: {bcc_address}\n")

    @noarg.command
    def goodbye(*, path: Annotated[Optional[str], noarg.arg.missing("~/goodbye.log")] = None) -> None:
        """
        writes a goodbye
        :param path: [-p] path to log to
        """
        iobuf.write(f"path: {path}\n")

    @noarg.command
    def handle_it(squared: Annotated[int, noarg.arg.handler(lambda x: int(x) ** 2)] = 0):
        """
        magical int squaring
        :param squared: int to square
        """
        iobuf.write(f"squared: {squared}\n")

    @noarg.command
    def say_alt(which: Annotated[str, noarg.arg.choices("hi", "bye")]) -> None:
        """
        say hi or bye
        :param which: which to say
        """
        iobuf.write(f"which: {which}\n")

    return cast(dict[str, Callable], {k: v for k, v in locals().items() if k != "iobuf"})
