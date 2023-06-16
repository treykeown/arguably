from __future__ import annotations

import enum
import inspect
from dataclasses import dataclass, field
from typing import Callable, Any, Union, Optional, List, Dict, Tuple

import arguably._modifiers as mods
import arguably._util as util


class InputMethod(enum.Enum):
    """Specifies how a given argument is passed in"""

    REQUIRED_POSITIONAL = 0  # usage: foo BAR
    OPTIONAL_POSITIONAL = 1  # usage: foo [BAR]
    OPTION = 2  # Examples: -F, --test_scripts, --filename foo.txt

    @property
    def is_positional(self) -> bool:
        return self in [InputMethod.REQUIRED_POSITIONAL, InputMethod.OPTIONAL_POSITIONAL]

    @property
    def is_optional(self) -> bool:
        return self in [InputMethod.OPTIONAL_POSITIONAL, InputMethod.OPTION]


@dataclass
class CommandDecoratorInfo:
    """Used for keeping a reference to everything marked with @arguably.command"""

    function: Callable
    alias: Optional[str] = None
    help: bool = True
    name: str = field(init=False)

    def __post_init__(self) -> None:
        if self.function.__name__ == "__root__":
            self.name = "__root__"
        else:
            self.name = util.normalize_name(self.function.__name__)


@dataclass
class SubtypeDecoratorInfo:
    """Used for keeping a reference to everything marked with @arguably.subtype"""

    type_: type
    alias: Optional[str] = None
    ignore: bool = False
    factory: Optional[Callable] = None


@dataclass
class CommandArg:
    """A single argument to a given command"""

    func_arg_name: str
    cli_arg_name: str

    input_method: InputMethod
    is_variadic: bool
    arg_value_type: type

    description: str
    alias: Optional[str] = None
    metavars: Optional[List[str]] = None

    default: Any = util.NoDefault

    modifiers: List[mods.CommandArgModifier] = field(default_factory=list)

    @staticmethod
    def _normalize_type_union(
        function_name: str,
        param: inspect.Parameter,
        value_type: type,
    ) -> type:
        """
        We break this out because Python 3.10 seems to want to wrap `Annotated[Optional[...` in another `Optional`, so
        we call this twice.
        """
        if isinstance(value_type, util.UnionType) or util.get_origin(value_type) is Union:
            filtered_types = [x for x in util.get_args(value_type) if x is not type(None)]
            if len(filtered_types) != 1:
                raise util.ArguablyException(
                    f"Function parameter `{param.name}` in `{function_name}` is an unsupported type. It must be either "
                    f"a single, non-generic type or a Union with None."
                )
            value_type = filtered_types[0]
        return value_type

    @staticmethod
    def normalize_type(
        function_name: str,
        param: inspect.Parameter,
        hints: Dict[str, Any],
    ) -> Tuple[type, List[mods.CommandArgModifier]]:
        """
        Normalizes the function argument type. Most of the logic here is validation. Explanation of what's returned for
        a given function argument type:
          * SomeType                    ->  value_type=SomeType, modifiers=[]
          * int | None                  ->  value_type=int, modifiers=[]
          * Tuple[float, float]         ->  value_type=type(None), modifiers=[_TupleModifier([float, float])]
          * List[str]                   ->  value_type=str, modifiers=[_ListModifier()]
          * Annotated[int, arg.count()] ->  value_type=int, modifiers=[_CountedModifier()]

        Things that will cause an exception:
          * Parameterized type other than a Optional[] or Tuple[]
          * Flexible-length Tuple[SomeType, ...]
          * Parameter lacking an annotation
        """

        modifiers: List[mods.CommandArgModifier] = list()

        if param.name in hints:
            value_type = hints[param.name]
        else:
            # No type hint. Guess type from default value, if any other than None. Otherwise, default to string.
            value_type = type(param.default) if param.default not in [param.empty, None] else str

        # Extra call to normalize a union here, see note in `_normalize_type_union`
        value_type = CommandArg._normalize_type_union(function_name, param, value_type)

        # Handle annotated types
        if util.get_origin(value_type) == util.Annotated:
            type_args = util.get_args(value_type)
            if len(type_args) == 0:
                raise util.ArguablyException(
                    f"Function parameter `{param.name}` is Annotated, but no type is specified"
                )
            else:
                value_type = type_args[0]
            for type_arg in type_args[1:]:
                if not isinstance(type_arg, mods.CommandArgModifier):
                    raise util.ArguablyException(
                        f"Function parameter `{param.name}` has an invalid annotation value: {type_arg}"
                    )
                modifiers.append(type_arg)

        # Normalize Union with None
        value_type = CommandArg._normalize_type_union(function_name, param, value_type)

        # Validate list/tuple and error on other parameterized types
        origin = util.get_origin(value_type)
        if (isinstance(value_type, type) and issubclass(value_type, list)) or (
            isinstance(origin, type) and issubclass(origin, list)
        ):
            type_args = util.get_args(value_type)
            if len(type_args) == 0:
                value_type = str
            elif len(type_args) > 1:
                raise util.ArguablyException(
                    f"Function parameter `{param.name}` in `{function_name}` has too many items passed to List[...]."
                    f"There should be exactly one item between the square brackets."
                )
            else:
                value_type = type_args[0]
            modifiers.append(mods.ListModifier())
        elif (isinstance(value_type, type) and issubclass(value_type, tuple)) or (
            isinstance(origin, type) and issubclass(origin, tuple)
        ):
            if param.kind in [param.VAR_KEYWORD, param.VAR_POSITIONAL]:
                raise util.ArguablyException(
                    f"Function parameter `{param.name}` in `{function_name}` is an *args or **kwargs, which should "
                    f"be annotated with what only one of its items should be."
                )
            type_args = util.get_args(value_type)
            if len(type_args) == 0:
                raise util.ArguablyException(
                    f"Function parameter `{param.name}` in `{function_name}` is a tuple but doesn't specify the "
                    f"type of its items, which arguably requires."
                )
            if type_args[-1] is Ellipsis:
                raise util.ArguablyException(
                    f"Function parameter `{param.name}` in `{function_name}` is a variable-length tuple, which is "
                    f"not supported."
                )
            value_type = type(None)
            modifiers.append(mods.TupleModifier(list(type_args)))
        elif origin is not None:
            if param.kind in [param.VAR_KEYWORD, param.VAR_POSITIONAL]:
                raise util.ArguablyException(
                    f"Function parameter `{param.name}` in `{function_name}` is an *args or **kwargs, which should "
                    f"be annotated with what only one of its items should be."
                )
            raise util.ArguablyException(
                f"Function parameter `{param.name}` in `{function_name}` is a generic type "
                f"(`{util.get_origin(value_type)}`), which is not supported."
            )

        return value_type, modifiers


@dataclass
class Command:
    """A fully processed command"""

    function: Callable
    name: str
    args: List[CommandArg]
    description: str = ""
    alias: Optional[str] = None
    add_help: bool = True

    arg_map: Dict[str, CommandArg] = field(init=False)

    def __post_init__(self) -> None:
        self.arg_map = dict()
        for arg in self.args:
            assert arg.func_arg_name not in self.arg_map
            if arg.cli_arg_name in self.arg_map:
                raise util.ArguablyException(
                    f"Function parameter `{arg.func_arg_name}` in `{self.name}` conflicts with "
                    f"`{self.arg_map[arg.cli_arg_name].func_arg_name}`, both names simplify to `{arg.cli_arg_name}`"
                )
            self.arg_map[arg.cli_arg_name] = arg
            self.arg_map[arg.func_arg_name] = arg

    def call(self, parsed_args: Dict[str, Any]) -> Any:
        """Filters arguments from argparse to only include the ones used by this command, then calls it"""

        args = list()
        kwargs = dict()

        filtered_args = {k: v for k, v in parsed_args.items() if k in self.arg_map}

        # Add to either args or kwargs
        for arg in self.args:
            if arg.input_method.is_positional and not arg.is_variadic:
                args.append(filtered_args[arg.cli_arg_name])
            elif arg.input_method.is_positional and arg.is_variadic:
                args.extend(filtered_args[arg.cli_arg_name])
            else:
                kwargs[arg.func_arg_name] = filtered_args[arg.func_arg_name]

        # Call the function
        return self.function(*args, **kwargs)

    def get_subcommand_metavar(self, command_metavar: str) -> str:
        """If this command has a subparser (for subcommands of its own), this can be called to generate a unique name
        for the subparser's command metavar"""
        if self.name == "__root__":
            return command_metavar
        return f"{self.name.replace(' ', '_')}{'_' if len(self.name) > 0 else ''}{command_metavar}"
