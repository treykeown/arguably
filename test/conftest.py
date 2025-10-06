from __future__ import annotations

import abc
import asyncio
import dataclasses
import io
import re
import sys
from io import StringIO
from pathlib import Path
from typing import Generator, Callable, cast, Optional, List, Dict, Tuple

import pytest

import arguably
from . import MANUAL, Permissions, PermissionsAlt, HiBye

from typing_extensions import Annotated


########################################################################################################################
# instrumentation


@pytest.fixture(autouse=True)
def arguably_context(request) -> Generator:
    # reset arguably
    arguably._context.context.reset()

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
    @arguably.command
    def basic():
        iobuf.write("basic\n")

    return basic


########################################################################################################################
# hello


@pytest.fixture
def fn_hello(iobuf: StringIO) -> Callable:
    @arguably.command
    def hello(name, age=30, *, howdy=False, lastname=None) -> None:
        """
        says hello to you
        :param name: your name
        :param age: your age
        :param howdy: [-H/--hwdy] say howdy instead of hello
        :param lastname: [-l] your {SURNAME}
        """
        greeting = "Howdy" if howdy else "Hello"
        if lastname is None:
            lastname = ""
        iobuf.write(f"{greeting}, {name} {lastname}! You'll be {age + 1} next year.\n")

    return hello


########################################################################################################################
# async_hello


@pytest.fixture
def fn_async_hello(iobuf: StringIO) -> Callable:
    @arguably.command
    async def async_hello(name, age=30, *, howdy=False, lastname=None) -> None:
        """
        says hello to you, asynchronously
        :param name: your name
        :param age: your age
        :param howdy: [-H] say howdy instead of hello
        :param lastname: [-l] your {SURNAME}
        """
        await asyncio.sleep(0.1)
        greeting = "Howdy" if howdy else "Hello"
        if lastname is None:
            lastname = ""
        iobuf.write(f"{greeting}, {name} {lastname}! You'll be {age + 1} next year.\n")

    return async_hello


########################################################################################################################
# enum


@pytest.fixture
def fn_chmod(iobuf: StringIO) -> Callable:
    @arguably.command
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
    @arguably.command
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
    @arguably.command
    def say(which: HiBye) -> None:
        """
        say hi or bye
        :param which: which to say
        """
        iobuf.write(f"{which.value}")

    return say


@pytest.fixture
def fn_say_annotated_enum(iobuf: StringIO) -> Callable:
    @arguably.command
    def say_enum(which: Annotated[HiBye, arguably.arg.choices(HiBye.HI, HiBye.BYE)]) -> None:
        """
        say hi or bye
        :param which: which to say
        """
        iobuf.write(f"which: {which.value}\n")

    return say_enum


########################################################################################################################
# advanced


@pytest.fixture
def scope_advanced(iobuf: StringIO) -> Dict[str, Callable]:
    @arguably.command
    def __root__(*, loud: bool = False):
        """
        advanced test
        :param loud: make it loud
        """
        if not MANUAL:
            assert not arguably.is_target()
        iobuf.write("> root\n")

        if loud:
            iobuf.write("__root__ loud\n")

    @arguably.command
    def add(*numbers: Annotated[int, arguably.arg.required()], coords: Optional[Tuple[int, int, int]] = None) -> None:
        """
        adds a bunch of numbers together
        :param numbers: the numbers {NUMS} to add
        :param coords: [-c] coordinates {X,Y,Z} updated with the sum
        """
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> add\n")

        total = sum(numbers)
        iobuf.write(f"add sum: {total}\n")
        if coords is not None:
            iobuf.write(f"add coords: {coords[0]+total}, {coords[1]+total}, {coords[2]+total}\n")

    @arguably.command
    def mixed_tuple(val: Tuple[str, int, float]) -> None:
        """
        mixed tuple
        :param val: the values
        """
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> mixed-tuple\n")

        iobuf.write(f"{repr(val[0])}, {repr(val[1])}, {repr(val[2])}\n")

    @arguably.command
    def ellipsis_tuple_floats(values: tuple[float, ...]) -> None:
        """
        ellipsis tuple of floats
        :param values: the float values
        """
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> ellipsis-tuple-floats\n")
        iobuf.write(f"{values}\n")
        iobuf.write(f"type: {type(values).__name__}\n")

    @arguably.command
    def ellipsis_tuple_ints(*, nums: tuple[int, ...] = ()) -> None:
        """
        ellipsis tuple of ints as option
        :param nums: the int values
        """
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> ellipsis-tuple-ints\n")
        iobuf.write(f"{nums}\n")
        iobuf.write(f"type: {type(nums).__name__}\n")

    @arguably.command
    def ellipsis_tuple_strings(values: tuple[str, ...]) -> None:
        """
        ellipsis tuple of strings
        :param values: the string values
        """
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> ellipsis-tuple-strings\n")
        iobuf.write(f"{values}\n")
        iobuf.write(f"type: {type(values).__name__}\n")

    @arguably.command
    def nested_tuple_ints(data: tuple[tuple[int, ...], ...]) -> None:
        """
        nested tuple of ints
        :param data: nested int tuples
        """
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> nested-tuple-ints\n")
        iobuf.write(f"{data}\n")
        iobuf.write(f"type: {type(data).__name__}\n")
        for i, inner_tuple in enumerate(data):
            iobuf.write(f"inner[{i}]: {inner_tuple} (type: {type(inner_tuple).__name__})\n")

    @arguably.command
    def nested_tuple_strings(*, values: tuple[tuple[str, ...], ...] = ()) -> None:
        """
        nested tuple of strings as option
        :param values: nested string tuples
        """
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> nested-tuple-strings\n")
        iobuf.write(f"{values}\n")
        iobuf.write(f"type: {type(values).__name__}\n")
        for i, inner_tuple in enumerate(values):
            iobuf.write(f"inner[{i}]: {inner_tuple} (type: {type(inner_tuple).__name__})\n")

    @arguably.command
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
        if arguably.is_target():
            iobuf.write("give is main\n")

    @arguably.command(alias="a")
    def give__ascii() -> None:
        """gives ascii"""
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> give ascii\n")

    @arguably.command
    def give__zen(
        *,
        rotten: bool = False,
    ) -> None:
        """
        gives zen
        :param rotten: makes the zen rotten
        """
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> give zen\n")

        if rotten:
            iobuf.write("give zen rotten\n")

    @arguably.command
    def do__a_dance() -> None:
        """
        does a dance
        """
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> do a-dance\n")

    @arguably.command(alias="h")
    def hey_you(
        name: str,
    ) -> None:
        """
        says hello to you
        :param name: your name
        """
        if not MANUAL:
            assert arguably.is_target()
        iobuf.write("> hey-you\n")
        iobuf.write(f"hey-you name: {name}")

    return cast(Dict[str, Callable], {k: v for k, v in locals().items() if k != "iobuf"})


########################################################################################################################
# annotated


@pytest.fixture
def scope_annotated(iobuf: StringIO) -> Dict[str, Callable]:
    class Logger(abc.ABC):
        @abc.abstractmethod
        def log(self, message: str) -> None:
            """log somewhere"""

        def __repr__(self):
            return f"{self.__class__.__name__}()"

    @arguably.subtype(alias="none")
    class NoLogger(Logger):
        """will not log"""

        def log(self, message: str) -> None:
            iobuf.write(f"~none: {message}\n")

    @arguably.subtype(alias="term")
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

    arguably.subtype(FileLogger, alias="file")

    @dataclasses.dataclass
    class Complex:
        foo: int
        bar: str

    # Insert classes into the global namespace, needed because we test with `from __future__ import annotations`
    # From https://stackoverflow.com/a/69034361:
    #   For the uncommon case of classes defined in a locals scope one has to explicitly provide the namespace.
    for local_name, local_item in locals().items():
        if re.match("^[A-Z]", local_name):
            globals()[local_name] = local_item

    @arguably.command
    def log(message: str = "Howdy, there!", *, logger: Annotated[Logger, arguably.arg.builder()] = NoLogger()) -> None:
        """
        logs a hello
        :param message: message to log
        :param logger: what to use for logging
        """
        logger.log(message)

    @arguably.command
    def multi_log(
        message: str = "Howdy, there!", *, logger: Annotated[List[Logger], arguably.arg.builder()] = [NoLogger()]
    ) -> None:
        """
        logs a hello
        :param message: message to log
        :param logger: what to use for logging
        """
        for lg in logger:
            lg.log(message)

    @arguably.command
    def dataclass(dc: Annotated[Complex, arguably.arg.builder()]) -> None:
        """
        build a dataclass
        :param dc: spec for dataclass
        """
        iobuf.write(f"dataclass: {dc}\n")

    @arguably.command
    def explain(*, verbose: Annotated[int, arguably.arg.count()] = 0):
        """
        explain something
        :param verbose: [-v] be verbose
        """
        iobuf.write(f"verbosity: {verbose}\n")

    @arguably.command
    def high_five(*people: Annotated[str, arguably.arg.required()]):
        """
        high-fives people
        :param people: who to high-five
        """
        iobuf.write(f"people: {','.join(people)}\n")

    @arguably.command
    def email_alt(
        from_: str,
        cc: List[str],
        *to: str,
        bcc: Optional[List[str]] = None,
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

    @arguably.command
    def email(
        from_: str,
        *to: Annotated[str, arguably.arg.required()],
        cc: List[str],
        bcc: Optional[List[str]] = None,
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

    @arguably.command
    def goodbye(*, path: Annotated[Optional[str], arguably.arg.missing("~/goodbye.log")] = None) -> None:
        """
        writes a goodbye
        :param path: [-p] path to log to
        """
        iobuf.write(f"path: {path}\n")

    @arguably.command
    def handle_it(squared: Annotated[int, arguably.arg.handler(lambda x: int(x) ** 2)] = 0):
        """
        magical int squaring
        :param squared: int to square
        """
        iobuf.write(f"squared: {squared}\n")

    @arguably.command
    def say_alt(which: Annotated[str, arguably.arg.choices("hi", "bye")]) -> None:
        """
        say hi or bye
        :param which: which to say
        """
        iobuf.write(f"which: {which}\n")

    return cast(Dict[str, Callable], {k: v for k, v in locals().items() if k != "iobuf"})
