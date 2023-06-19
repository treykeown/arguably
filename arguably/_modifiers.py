from __future__ import annotations

import abc
import enum
import inspect
from dataclasses import dataclass
from typing import Callable, Any, Union, List, Dict, Tuple

import arguably._argparse_extensions as ap_ext
import arguably._commands as cmds
import arguably._util as util


@dataclass(frozen=True)
class CommandArgModifier(abc.ABC):
    """A class that encapsulates a change to the kwargs dict to be passed to parser.add_argument()"""

    def check_valid(self, value_type: type, param: inspect.Parameter, function_name: str) -> None:
        """Checks whether this modifier is valid for the parameter"""

    @abc.abstractmethod
    def modify_arg_dict(self, command: cmds.Command, arg_: cmds.CommandArg, kwargs_dict: Dict[str, Any]) -> None:
        """Modifies the kwargs passed to parser.add_argument()"""


@dataclass(frozen=True)
class MissingArgDefaultModifier(CommandArgModifier):
    """Allows an option to be a flag, passing a default value instead of a value provided via the command line"""

    missing_value: Any

    def modify_arg_dict(self, command: cmds.Command, arg_: cmds.CommandArg, kwargs_dict: Dict[str, Any]) -> None:
        kwargs_dict.update(nargs="?", const=self.missing_value)


@dataclass(frozen=True)
class CountedModifier(CommandArgModifier):
    """Counts the number of times a flag is provided"""

    def modify_arg_dict(self, command: cmds.Command, arg_: cmds.CommandArg, kwargs_dict: Dict[str, Any]) -> None:
        if arg_.input_method != cmds.InputMethod.OPTION:
            raise util.ArguablyException(
                f"`arguably.Counted` should only be used on {cmds.InputMethod.OPTION.name}, but was used on "
                f"{arg_.func_arg_name}, which is {arg_.input_method.name}."
            )
        kwargs_dict.update(action="count")
        if "type" in kwargs_dict:
            del kwargs_dict["type"]
        if "nargs" in kwargs_dict:
            del kwargs_dict["nargs"]


@dataclass(frozen=True)
class RequiredModifier(CommandArgModifier):
    """Marks an input as required. In the case of a variadic positional arg, uses the '+' symbol to represent this."""

    def check_valid(self, value_type: type, param: inspect.Parameter, function_name: str) -> None:
        if issubclass(value_type, bool):
            raise util.ArguablyException("Cannot mark a bool as required.")

    def modify_arg_dict(self, command: cmds.Command, arg_: cmds.CommandArg, kwargs_dict: Dict[str, Any]) -> None:
        if arg_.is_variadic:
            kwargs_dict.update(nargs="+")
            if "default" in kwargs_dict:
                del kwargs_dict["default"]
        else:
            kwargs_dict.update(required=True)


@dataclass(frozen=True)
class ListModifier(CommandArgModifier):
    """Sets up arguably list handling. Sensitive to the `_RequiredModifier`."""

    def modify_arg_dict(self, command: cmds.Command, arg_: cmds.CommandArg, kwargs_dict: Dict[str, Any]) -> None:
        if arg_.input_method is cmds.InputMethod.OPTIONAL_POSITIONAL:
            kwargs_dict.update(nargs="?")
        if arg_.input_method is not cmds.InputMethod.REQUIRED_POSITIONAL:
            kwargs_dict.update(default=list())
        if (arg_.default is util.NoDefault and arg_.input_method is cmds.InputMethod.OPTION) or RequiredModifier in [
            type(mod) for mod in arg_.modifiers
        ]:
            kwargs_dict.update(required=True)
        kwargs_dict.update(action=ap_ext.ListTupleBuilderAction, command_arg=arg_)


@dataclass(frozen=True)
class TupleModifier(CommandArgModifier):
    """Sets up arguably tuple handling"""

    tuple_arg: List[type]

    def modify_arg_dict(self, command: cmds.Command, arg_: cmds.CommandArg, kwargs_dict: Dict[str, Any]) -> None:
        if arg_.metavars is None:
            kwargs_dict.update(metavar=",".join([arg_.cli_arg_name] * len(self.tuple_arg)))
        kwargs_dict.update(action=ap_ext.ListTupleBuilderAction, command_arg=arg_, type=self.tuple_arg)


@dataclass(frozen=True)
class BuilderModifier(CommandArgModifier):
    """Sets up arguably builder"""

    def modify_arg_dict(self, command: cmds.Command, arg_: cmds.CommandArg, kwargs_dict: Dict[str, Any]) -> None:
        kwargs_dict.update(action=ap_ext.ListTupleBuilderAction, command_arg=arg_)


@dataclass(frozen=True)
class HandlerModifier(CommandArgModifier):
    """
    Allows full user control over how an input is handled, a function should be passed in to parse the string from the
    command line
    """

    handler: Callable[[str], Any]

    def modify_arg_dict(self, command: cmds.Command, arg_: cmds.CommandArg, kwargs_dict: Dict[str, Any]) -> None:
        kwargs_dict.update(type=self.handler)


@dataclass(frozen=True)
class ChoicesModifier(CommandArgModifier):
    """Restricts inputs to one of a given set of choices"""

    choices: Tuple[Union[str, enum.Enum], ...]

    def check_valid(self, value_type: type, param: inspect.Parameter, function_name: str) -> None:
        if len(self.choices) == 0:
            raise util.ArguablyException("At least one choice is required for `arguably.arg.choices()`")

        first_type = type(self.choices[0])
        if not all(issubclass(type(c), first_type) or issubclass(first_type, type(c)) for c in self.choices):
            raise util.ArguablyException("Choices must all be of the same type")

        for choice in self.choices:
            if not isinstance(choice, value_type):
                raise util.ArguablyException(
                    f"Function argument `{param.name}` in `{function_name}` specifies choices, but choice {choice} is "
                    f"not a subtype of {value_type}."
                )

    def modify_arg_dict(self, command: cmds.Command, arg_: cmds.CommandArg, kwargs_dict: Dict[str, Any]) -> None:
        kwargs_dict.update(choices=self.choices)
