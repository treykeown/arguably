from __future__ import annotations

import asyncio
import enum
import inspect
import re
from dataclasses import dataclass, field
from typing import Callable, Any, Union, Optional, List, Dict, Tuple, cast

from docstring_parser import parse as docparse

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
    command: Command = field(init=False)

    def __post_init__(self) -> None:
        if self.function.__name__ == "__root__":
            self.name = "__root__"
        else:
            self.name = util.normalize_name(self.function.__name__)

        self.command = self._process()

    def _process(self) -> Command:
        """Takes the decorator info and return a processed command"""

        processed_name = self.name
        func = self.function.__init__ if isinstance(self.function, type) else self.function  # type: ignore[misc]

        # Get the description from the docstring
        if func.__doc__ is None:
            docs = None
            processed_description = ""
        else:
            docs = docparse(func.__doc__)
            processed_description = "" if docs.short_description is None else docs.short_description

        try:
            hints = util.get_type_hints(func, include_extras=True)
        except NameError as e:
            hints = {}
            util.warn(f"Unable to resolve type hints for function {processed_name}: {str(e)}", func)

        # Will be filled in as we loop over all parameters
        processed_args: List[CommandArg] = list()

        # Iterate over all parameters
        for func_arg_name, param in inspect.signature(self.function).parameters.items():
            cli_arg_name = util.normalize_name(func_arg_name, spaces=False)
            arg_default = util.NoDefault if param.default is param.empty else param.default

            # Handle variadic arguments
            is_variadic = False
            if param.kind is param.VAR_KEYWORD:
                raise util.ArguablyException(f"`{processed_name}` is using **kwargs, which is not supported")
            if param.kind is param.VAR_POSITIONAL:
                is_variadic = True

            # Get the type and normalize it
            arg_value_type, modifiers = CommandArg.normalize_type(processed_name, param, hints)
            tuple_modifiers = [m for m in modifiers if isinstance(m, mods.TupleModifier)]
            expected_metavars = 1
            if len(tuple_modifiers) > 0:
                assert len(tuple_modifiers) == 1
                expected_metavars = len(tuple_modifiers[0].tuple_arg)

            # Get the description
            arg_description = ""
            if docs is not None and docs.params is not None:
                ds_matches = [ds_p for ds_p in docs.params if ds_p.arg_name.lstrip("*") == param.name]
                if len(ds_matches) > 1:
                    raise util.ArguablyException(
                        f"Function parameter `{param.name}` in " f"`{processed_name}` has multiple docstring entries."
                    )
                if len(ds_matches) == 1:
                    ds_info = ds_matches[0]
                    arg_description = "" if ds_info.description is None else ds_info.description

            # Extract the alias
            arg_alias = None
            if alias_match := re.match(r"^\[-([a-zA-Z0-9])] ", arg_description):
                arg_description = arg_description[len(alias_match.group(0)) :]
                arg_alias = alias_match.group(1)

            # Extract the metavars
            metavars = None
            if metavar_split := re.split(r"\{((?:[a-zA-Z0-9_-]+(?:, *)*)+)}", arg_description):
                if len(metavar_split) == 3:
                    # format would be: ['pre-metavar', 'METAVAR', 'post-metavar']
                    match_items = [i.strip() for i in metavar_split[1].split(",")]
                    if is_variadic:
                        if len(match_items) != 1:
                            raise util.ArguablyException(
                                f"Function parameter `{param.name}` in `{processed_name}` should only have one item in "
                                f"its metavar descriptor, but found {len(match_items)}: {','.join(match_items)}."
                            )
                    elif len(match_items) != expected_metavars:
                        if len(match_items) == 1:
                            match_items *= expected_metavars
                        else:
                            raise util.ArguablyException(
                                f"Function parameter `{param.name}` in `{processed_name}` takes {expected_metavars} "
                                f"items, but metavar descriptor has {len(match_items)}: {','.join(match_items)}."
                            )
                    metavars = [i.upper() for i in match_items]
                    arg_description = "".join(metavar_split)  # Strips { and } from metavars for description
                if len(metavar_split) > 3:
                    raise util.ArguablyException(
                        f"Function parameter `{param.name}` in `{processed_name}` has multiple metavar sequences - "
                        f"these are denoted like {{A, B, C}}. There should be only one."
                    )

            # What kind of argument is this? Is it required-positional, optional-positional, or an option?
            if param.kind == param.KEYWORD_ONLY:
                input_method = InputMethod.OPTION
            elif arg_default is util.NoDefault:
                input_method = InputMethod.REQUIRED_POSITIONAL
            else:
                input_method = InputMethod.OPTIONAL_POSITIONAL

            # Check modifiers
            for modifier in modifiers:
                modifier.check_valid(arg_value_type, param, processed_name)

            # Finished processing this arg
            processed_args.append(
                CommandArg(
                    func_arg_name,
                    cli_arg_name,
                    input_method,
                    is_variadic,
                    arg_value_type,
                    arg_description,
                    arg_alias,
                    metavars,
                    arg_default,
                    modifiers,
                )
            )

        # Return the processed command
        return Command(
            self.function,
            processed_name,
            processed_args,
            processed_description,
            self.alias,
            self.help,
        )


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

    def get_options(self) -> Union[Tuple[()], Tuple[str], Tuple[str, str]]:
        if self.input_method is InputMethod.OPTION:
            return cast(Tuple[()], tuple())
        elif self.alias is None:
            return (f"--{self.cli_arg_name}",)
        else:
            return f"-{self.alias}", f"--{self.cli_arg_name}"

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
        if util.is_async_callable(self.function):
            return asyncio.get_event_loop().run_until_complete(self.function(*args, **kwargs))
        else:
            return self.function(*args, **kwargs)

    def get_subcommand_metavar(self, command_metavar: str) -> str:
        """If this command has a subparser (for subcommands of its own), this can be called to generate a unique name
        for the subparser's command metavar"""
        if self.name == "__root__":
            return command_metavar
        return f"{self.name.replace(' ', '_')}{'_' if len(self.name) > 0 else ''}{command_metavar}"
