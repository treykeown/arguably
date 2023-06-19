from __future__ import annotations

import argparse
import enum
import inspect
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, TextIO, Union, Optional, List, Dict, Type, Tuple, Callable, Iterator, cast

from ._argparse_extensions import HelpFormatter, FlagAction, ArgumentParser
from ._commands import CommandDecoratorInfo, SubtypeDecoratorInfo, Command, CommandArg, InputMethod
from ._modifiers import TupleModifier, ListModifier
from ._util import (
    logger,
    log_args,
    ArguablyException,
    normalize_name,
    NoDefault,
    get_type_hints,
    info_for_flags,
    get_ancestors,
    get_parser_name,
    warn,
    func_info,
)


@dataclass
class _ContextOptions:
    name: Optional[str]

    # Behavior options
    always_subcommand: bool
    version_flag: Union[bool, Tuple[str], Tuple[str, str]]
    strict: bool

    # Formatting options
    show_defaults: bool
    show_types: bool
    command_metavar: str
    max_description_offset: int
    max_width: int
    output: Optional[TextIO]

    def __post_init__(self) -> None:
        # When running as a module, show the script name as the module path.
        # Otherwise, use default argparse behavior
        if self.name is None:
            try:
                import importlib.util

                self.name = importlib.util.find_spec("__main__").name  # type: ignore[union-attr]
            except (ValueError, AttributeError):
                self.name = None

    def get_version_flags(self) -> Union[Tuple[()], Tuple[str], Tuple[str, str]]:
        if self.version_flag is False:
            return cast(Tuple[()], tuple())
        elif self.version_flag is True:
            return ("--version",)
        else:
            return self.version_flag


class _Context:
    """Singleton, used for storing arguably state."""

    def __init__(self) -> None:
        # These are `None` right now, they're set during `run()`. No methods making use of them are called before then.
        self._options: _ContextOptions = None  # type: ignore[assignment]
        self._extra_argparser_options: Dict[str, Any] = None  # type: ignore[assignment]

        # Info for all invocations of `@arguably.command`
        self._command_decorator_info: List[CommandDecoratorInfo] = list()

        # Info for all invocations of `@arguably.subtype`
        self._subtype_init_info: List[SubtypeDecoratorInfo] = list()

        # Stores mapping from normalized names for an enum type to an enum value
        self._enum_mapping: Dict[Type[enum.Enum], Dict[str, enum.Enum]] = dict()

        # Stores which flag arguments have had their default value cleared
        self._enum_flag_default_cleared: set[Tuple[argparse.ArgumentParser, str]] = set()

        # Are we currently calling the targeted command (or just an ancestor?)
        self._is_calling_target = True

        # Used for handling `error()`, keeps a reference to the parser for the current command
        self._current_parser: Optional[argparse.ArgumentParser] = None

        # These are really only set and used in the run() method
        self._commands: Dict[str, Command] = dict()
        self._command_aliases: Dict[str, str] = dict()
        self._parsers: Dict[str, argparse.ArgumentParser] = dict()
        self._subparsers: Dict[str, Any] = dict()

    def reset(self) -> None:
        self.__dict__.clear()
        self.__init__()  # type: ignore[misc]

    def add_command(self, **kwargs: Any) -> None:
        """Invoked by `@arguably.command`, saves info about a command to include when the parser is set up."""
        info = CommandDecoratorInfo(**kwargs)
        self._command_decorator_info.append(info)

    def add_subtype(self, **kwargs: Any) -> None:
        """Invoked by `@arguably.subtype`, saves info about a how to construct a type."""
        type_ = SubtypeDecoratorInfo(**kwargs)
        self._subtype_init_info.append(type_)

    def find_subtype(self, func_arg_type: type) -> List[SubtypeDecoratorInfo]:
        return [bi for bi in self._subtype_init_info if issubclass(bi.type_, func_arg_type)]

    def is_target(self) -> bool:
        """
        Only useful if `invoke_ancestors=True`. Returns `True` if the targeted command is being executed and `False` if
        not. This is safe to call even if `arguably` is not being used, since it returns `True` if `arguably.run()` is
        not being used.

        Returns:
            `False` if `arguably.run()` was called and the currently running command is not the targeted command, `True`
                in every other case.

        Examples:
            ```python
            import arguably

            @arguably.command
            def __root__(*, config_file=None):
                print(f"Using config {config_file}")
                if not arguably.is_target():
                    return
                print("__root__ is the target!")

            @arguably.command
            def hi():
                print("hi is the target!")

            @arguably.command
            def bye():
                print("bye is the target!")

            if __name__ == "__main__":
                arguably.run()
            ```

            ```console
            user@machine:~$ python3 is_target.py --config-file foo.yml
            Using config foo.yml
            __root__ is the target!
            ```

            ```console
            user@machine:~$ python3 is_target.py --config-file foo.yml hi
            Using config foo.yml
            hi is the target!
            ```
        """
        return self._is_calling_target

    def check_and_set_enum_flag_default_status(self, parser: argparse.ArgumentParser, cli_arg_name: str) -> bool:
        key = (parser, cli_arg_name)
        present = key in self._enum_flag_default_cleared
        self._enum_flag_default_cleared.add(key)
        return present

    def _formatter(self, prog: str) -> HelpFormatter:
        """HelpFormatter for argparse, hooks up our max_name_width and max_width options."""
        return HelpFormatter(
            prog, max_help_position=self._options.max_description_offset, width=self._options.max_width
        )

    def set_up_enum(
        self, enum_type: Type[enum.Enum], members: Optional[List[enum.Enum]] = None
    ) -> Dict[str, enum.Enum]:
        if enum_type not in self._enum_mapping:
            enum_name_dict: Dict[str, enum.Enum] = dict()
            self._enum_mapping[enum_type] = enum_name_dict

            for enum_item in enum_type:
                if members is not None and enum_item not in members:
                    continue
                enum_name = normalize_name(enum_item.name, spaces=False)
                if enum_name in enum_name_dict:
                    raise ArguablyException(
                        f"Normalized name {enum_name} already taken for enum {enum_type.__name__} by "
                        f"{enum_name_dict[enum_name]}"
                    )
                enum_name_dict[enum_name] = enum_item

        return self._enum_mapping[enum_type]

    def get_enum_mapping(self, enum_type: Type[enum.Enum]) -> Dict[str, enum.Enum]:
        assert enum_type in self._enum_mapping
        return self._enum_mapping[enum_type]

    def _validate_args(self, cmd: Command, is_root_cmd: bool) -> None:
        """Validates all arguments that will be added to the parser for a given command"""

        for arg_ in cmd.args:
            arg_aliases = arg_.get_options()

            # Validate no conflict with `--version` flag (or whatever it was set to)
            if is_root_cmd:
                version_flags = self._options.get_version_flags()
                conflicts = [opt for opt in arg_aliases if opt in version_flags]
                if len(conflicts) > 0:
                    raise ArguablyException(
                        f"Function argument `{arg_.func_arg_name}` in `{cmd.name}` conflicts with version flag."
                        f"Conflicting items: {', '.join(conflicts)}"
                    )

            # Validate no conflicts with `-h/--help`
            if cmd.add_help:
                help_flags = ("-h", "--help")
                conflicts = [opt for opt in arg_aliases if opt in help_flags]
                if len(conflicts) > 0:
                    raise ArguablyException(
                        f"Function argument `{arg_.func_arg_name}` in `{cmd.name}` conflicts with help flag."
                        f"Conflicting items: {', '.join(conflicts)}"
                    )

            # Validate positional arg names
            if arg_.input_method.is_positional:
                if arg_.func_arg_name == self._options.command_metavar:
                    raise ArguablyException(
                        f"Function argument `{arg_.func_arg_name}` in `{cmd.name}` is named the same as "
                        f"`command_metavar`. Either change the parameter name or set the `command_metavar` option to "
                        f"something other than `{arg_.func_arg_name}` when calling arguably.run()"
                    )

            # Validate `enum.Flag`
            if issubclass(arg_.arg_value_type, enum.Flag):
                if arg_.input_method.is_positional:
                    raise ArguablyException(
                        f"Function argument `{arg_.func_arg_name}` in `{cmd.name}` is both positional and an enum.Flag."
                        f" Positional enum flags are unsupported, since they are turned into options."
                    )
                if arg_.default is NoDefault:
                    raise ArguablyException(
                        f"Function argument `{arg_.func_arg_name}` in `{cmd.name}` is an enum.Flag. Due to "
                        f"implementation limitations, all enum.Flag parameters must have a default value."
                    )

            # Validate `bool`
            if issubclass(arg_.arg_value_type, bool):
                if arg_.input_method is not InputMethod.OPTION or arg_.default is NoDefault:
                    raise ArguablyException(
                        f"Function parameter `{arg_.func_arg_name}` in `{cmd.name}` is a `bool`. Boolean parameters "
                        f"must have a default value and be an optional, not a positional, argument."
                    )

    def _set_up_args(self, cmd: Command) -> None:
        """Adds all arguments to the parser for a given command"""

        parser = self._parsers[cmd.name]

        for arg_ in cmd.args:
            # Short-circuit, different path for enum.Flag. We add multiple options, one for each flag entry
            if issubclass(arg_.arg_value_type, enum.Flag):
                parser.set_defaults(**{arg_.cli_arg_name: arg_.default})
                for entry in info_for_flags(arg_.cli_arg_name, arg_.arg_value_type):
                    argspec = log_args(
                        logger.debug,
                        f"Parser({repr(get_parser_name(parser.prog))}).",
                        parser.add_argument.__name__,
                        # Args for the call are below:
                        *entry.option,
                        action=FlagAction,
                        const=entry,
                        nargs=0,
                        help=entry.description,
                    )
                    parser.add_argument(*argspec.args, **argspec.kwargs)
                continue

            # Optional kwargs for parser.add_argument
            add_arg_kwargs: Dict[str, Any] = dict(type=arg_.arg_value_type)

            arg_description = arg_.description
            description_extras = []

            # Show arg type?
            if self._options.show_types:
                list_modifiers = [m for m in arg_.modifiers if isinstance(m, ListModifier)]
                tuple_modifiers = [m for m in arg_.modifiers if isinstance(m, TupleModifier)]
                if len(tuple_modifiers) > 0:
                    assert len(tuple_modifiers) == 1
                    type_name = f"({','.join(t.__name__ for t in tuple_modifiers[0].tuple_arg)})"
                else:
                    type_name = arg_.arg_value_type.__name__
                if len(list_modifiers) > 0:
                    assert len(list_modifiers) == 1
                    type_name = f"list[{type_name}]"
                description_extras.append(f"type: {type_name}")

            # `default` value?
            if arg_.input_method.is_optional and arg_.default is not NoDefault:
                add_arg_kwargs.update(default=arg_.default)
                if self._options.show_defaults:
                    if isinstance(arg_.default, enum.Enum):
                        description_extras.append(f"default: {normalize_name(arg_.default.name, spaces=False)}")
                    elif isinstance(arg_.default, str):
                        str_default = arg_.default
                        # Use the string repr if it contains spaces, contains a newline, or is zero-length
                        if (" " in str_default) or ("\n" in str_default) or (len(str_default) == 0):
                            str_default = repr(str_default)
                        description_extras.append(f"default: {str_default}")
                    else:
                        description_extras.append(f"default: {arg_.default}")

            # Number of arguments `nargs`?
            if arg_.is_variadic:
                add_arg_kwargs.update(nargs="*", default=list())
            elif arg_.input_method is InputMethod.OPTIONAL_POSITIONAL:
                add_arg_kwargs.update(nargs="?")

            # Any specified `metavar`s?
            if arg_.metavars is not None:
                if len(arg_.metavars) == 1:
                    add_arg_kwargs.update(metavar=arg_.metavars[0])
                else:
                    add_arg_kwargs.update(metavar=tuple(arg_.metavars))

            # Possible choices `choices`?
            if issubclass(arg_.arg_value_type, enum.Enum):
                mapping = self.set_up_enum(arg_.arg_value_type)
                add_arg_kwargs.update(choices=[n for n in mapping])

            cli_arg_names: Tuple[str, ...] = (arg_.cli_arg_name,)

            # Special handling for optional arguments
            if arg_.input_method is InputMethod.OPTION:
                cli_arg_names = (
                    (f"--{arg_.cli_arg_name}",) if arg_.alias is None else (f"-{arg_.alias}", f"--{arg_.cli_arg_name}")
                )

            # `bool` should be flags
            if issubclass(arg_.arg_value_type, bool):
                # Use `store_true` or `store_false` for bools
                add_arg_kwargs.update(action="store_true" if arg_.default is False else "store_false")
                if "type" in add_arg_kwargs:
                    del add_arg_kwargs["type"]

            # Set the help description
            if len(description_extras) > 0:
                if len(arg_description) > 0:
                    arg_description += " "
                arg_description += f"({', '.join(description_extras)})"
            add_arg_kwargs.update(help=arg_description)

            # Run modifiers for this arg
            for modifier in arg_.modifiers:
                modifier.modify_arg_dict(cmd, arg_, add_arg_kwargs)

            # Add the argument to the parser
            argspec = log_args(
                logger.debug,
                f"Parser({repr(get_parser_name(parser.prog))}).",
                parser.add_argument.__name__,
                # Args for the call are below:
                *cli_arg_names,
                **add_arg_kwargs,
            )
            parser.add_argument(*argspec.args, **argspec.kwargs)

    def _build_subparser_tree(self, command_decorator_info: CommandDecoratorInfo) -> str:
        """Builds up the subparser tree for a given `_CommandDecoratorInfo`. Inserts dummy entries to `self._parsers`
        and `self._commands` if necessary. Returns the name of the parent for this command."""

        prev_ancestor = "__root__"

        # Create tree of parsers and subparsers for ancestors
        ancestor_names = get_ancestors(command_decorator_info.name)
        for ancestor in ancestor_names:
            required_subparser = False
            if ancestor not in self._commands:
                # Dummy command - this ancestor doesn't have a function of its own, it's just a path.
                self._commands[ancestor] = Command(lambda *_, **__: None, ancestor, [])
            if ancestor not in self._parsers:
                # Dummy parser - since there's nothing to run, require the subparser.
                required_subparser = True
                argspec = log_args(
                    logger.debug,
                    f"Subparsers({repr(prev_ancestor)}).",
                    self._subparsers[prev_ancestor].add_parser.__name__,
                    # Args for the call are below:
                    ancestor.split(" ")[-1],
                    help="",
                    formatter_class=self._formatter,
                    **self._extra_argparser_options,
                )
                self._parsers[ancestor] = self._subparsers[prev_ancestor].add_parser(*argspec.args, **argspec.kwargs)
            if ancestor not in self._subparsers:
                # Add subparser to the parent command's parser.
                ancestor_cmd = self._commands[ancestor]
                if any(arg.input_method.is_positional for arg in ancestor_cmd.args):
                    raise ArguablyException(
                        f"Command `{ancestor}` cannot have both subcommands and positional arguments."
                    )
                argspec = log_args(
                    logger.debug,
                    f"Parser({repr(ancestor)}).",
                    self._parsers[ancestor].add_subparsers.__name__,
                    # Args for the call are below:
                    parser_class=ArgumentParser,
                    dest=ancestor_cmd.get_subcommand_metavar(self._options.command_metavar),
                    metavar=self._options.command_metavar,
                    required=required_subparser,
                )
                self._subparsers[ancestor] = self._parsers[ancestor].add_subparsers(*argspec.args, **argspec.kwargs)
            prev_ancestor = ancestor
        return prev_ancestor

    @contextmanager
    def current_parser(self, parser: argparse.ArgumentParser) -> Iterator[None]:
        last_parser = self._current_parser
        self._current_parser = parser
        try:
            yield
        finally:
            self._current_parser = last_parser

    def error(self, message: str) -> None:
        """
        Prints an error message and exits. Should be used when a CLI input is not of the correct form. `arguably`
        handles converting values to the correct type, but if extra validation is performed and fails, you should call
        this.

        Args:
            message: A message to be printed to the console indicating why the input is wrong.

        Raises:
            SystemExit: The script will exit.

        Examples:
            ```python
            #!/usr/bin/env python3
            import arguably

            @arguably.command
            def high_five(*people):
                if len(people) > 5:
                    arguably.error("Too many people to high-five!")
                for person in people:
                    print(f"High five, {person}!")

            if __name__ == "__main__":
                arguably.run()
            ```

            ```console
            user@machine:~$ python3 error.py Graham John Terry Eric Terry Michael
            usage: error.py [-h] [people ...]
            error.py: error: Too many people to high-five!
            ```
        """
        if self._current_parser is None:
            raise ArguablyException("Unknown current parser.")
        self._current_parser.error(message)  # This will exit the script

    def _soft_failure(self, msg: str, function: Optional[Callable] = None) -> None:
        if self._options.strict:
            if function is not None:
                info = func_info(function)
                if info is not None:
                    source_file, source_file_line = info
                    msg = f"({source_file}:{source_file_line}) {function.__name__}: {msg}"
            raise ArguablyException(msg)
        else:
            warn(msg, function)

    def run(
        self,
        name: Optional[str] = None,
        always_subcommand: bool = False,
        version_flag: Union[bool, Tuple[str], Tuple[str, str]] = False,
        strict: bool = True,
        show_defaults: bool = True,
        show_types: bool = True,
        max_description_offset: int = 60,
        max_width: int = 120,
        command_metavar: str = "command",
        output: Optional[TextIO] = None,
    ) -> Any:
        """
        Set up the argument parser, parse argv, and run the appropriate command(s)

        Args:
            name: Name of the script/program. Defaults to the filename or module name, depending on how the script is
                run. `$ python3 my/script.py` yields `script.py`, and `python3 -m my.script` yeilds `script`.
            always_subcommand: If true, will force a subcommand interface to be used, even if there's only one command.
            version_flag: If true, adds an option to show the script version using the value of `__version__` in the
                invoked script. If a tuple of one or two strings is passed in, like `("-V", "--ver")`, those are used
                instead of the default `--version`.
            strict: Will prevent the script from running if there are any `ArguablyException`s raised during CLI
                initialization.
            show_defaults: Show the default value (if any) for each argument at the end of its help string.
            show_types: Show the type of each argument at the end of its help string.
            max_description_offset: The maximum number of columns before argument descriptions are printed. Equivalent
                to `max_help_position` in argparse.
            max_width: The total maximum width of text to be displayed in the terminal. Equivalent to `width` in
                argparse.
            command_metavar: The name shown in the usage string for taking in a subcommand. Change this if you have a
                conflicting argument name.
            output: Where argparse output should be written - can write to a file, stderr, or anything similar.

        Returns:
            The return value from the called function.

        Examples:
            ```python
            #!/usr/bin/env python3
            \"\"\"description for this script'''
            from io import StringIO

            import arguably

            __version__ = "1.2.3"

            @arguably.command
            def example(): ...

            if __name__ == "__main__":
                output = StringIO()
                try:
                    arguably.run(
                        name="myname",
                        always_subcommand=True,
                        version_flag=True,
                        command_metavar="mycmd",
                        output=output
                    )
                finally:
                    print(f"Captured output length: {len(output.getvalue())=}")
                    print()
                    print(output.getvalue(), end="")
            ```

            ```console
            user@machine:~$ python3 run.py -h
            Captured output length: len(output.getvalue())=222

            usage: myname [-h] [--version] mycmd ...

            description for this script

            positional arguments:
              mycmd
                example

            options:
              -h, --help  show this help message and exit
              --version   show program's version number and exit
            ```

            ```console
            user@machine:~$ python3 run.py --version
            Captured output length: len(output.getvalue())=13

            myname 1.2.3
            ```
        """

        # Set options
        self._options = _ContextOptions(**{k: v for k, v in locals().items() if k != "self"})
        self._extra_argparser_options = dict(output=self._options.output)

        self._is_calling_target = False

        only_one_cmd = (len(self._command_decorator_info) == 1) and not self._options.always_subcommand

        # Grab the description
        import __main__

        description = "" if __main__.__doc__ is None else __main__.__doc__.partition("\n\n\n")[0]

        # TODO: Rewrite this code to remove the need for this line
        add_root_help = next(
            iter(info.help for info in self._command_decorator_info if info.name == "__root__" or only_one_cmd), True
        )

        # Set up the root parser
        argspec = log_args(
            logger.debug,
            f"Initializing {repr('__root__')} parser: ",
            ArgumentParser.__name__,
            # Args for the call are below:
            prog=self._options.name,
            description=description,
            formatter_class=self._formatter,
            add_help=add_root_help,
            **self._extra_argparser_options,
        )
        root_parser = ArgumentParser(*argspec.args, **argspec.kwargs)
        self._parsers["__root__"] = root_parser

        # Add version flags if necessary
        argparse_version_flags: Union[tuple, Tuple[str], Tuple[str, str]] = tuple()
        if self._options.version_flag:
            if not hasattr(__main__, "__version__"):
                self._soft_failure("__version__ must be defined if version_flag is set")
            else:
                argparse_version_flags = self._options.get_version_flags()
                version_string = f"%(prog)s {__main__.__version__}"
                argspec = log_args(
                    logger.debug,
                    f"Parser({repr('__root__')}).",
                    root_parser.add_argument.__name__,
                    # Args for the call are below:
                    *argparse_version_flags,
                    action="version",
                    version=version_string,
                )
                root_parser.add_argument(*argspec.args, **argspec.kwargs)

        # Check the number of commands we have
        if len(self._command_decorator_info) == 0:
            raise ArguablyException("At least one command is required")

        for command_decorator_info in sorted(
            self._command_decorator_info, key=lambda v: (v.name != "__root__", v.name.count(" "))
        ):
            if only_one_cmd:
                parent_name = "__root__"
                self._parsers[command_decorator_info.name] = self._parsers["__root__"]
            else:
                parent_name = self._build_subparser_tree(command_decorator_info)

            is_root = only_one_cmd or command_decorator_info.name == "__root__"
            cmd = command_decorator_info.command

            try:
                self._validate_args(cmd, is_root)
            except ArguablyException as e:
                self._soft_failure(str(e), cmd.function)
                continue

            # Save command and its alias to the dicts
            if cmd.name in self._commands:
                self._soft_failure(f"Name `{cmd.name}` is already taken", cmd.function)
                continue
            if cmd.alias is not None:
                if cmd.alias in self._command_aliases:
                    self._soft_failure(
                        f"Alias `{cmd.alias}` for `{cmd.name}` is already taken by "
                        f"`{self._command_aliases[cmd.alias]}`",
                        cmd.function,
                    )
                    continue
                self._command_aliases[cmd.alias] = cmd.name
            self._commands[cmd.name] = cmd

            # Add the parser for the command
            if not only_one_cmd and cmd.name != "__root__":
                argspec = log_args(
                    logger.debug,
                    f"Subparsers({repr(parent_name)}).",
                    self._subparsers[parent_name].add_parser.__name__,
                    # Args for the call are below:
                    cmd.name.split(" ")[-1],
                    aliases=[cmd.alias] if cmd.alias is not None else [],
                    help=cmd.description,
                    description=cmd.description,
                    formatter_class=self._formatter,
                    add_help=cmd.add_help,
                    **self._extra_argparser_options,
                )
                self._parsers[cmd.name] = self._subparsers[parent_name].add_parser(*argspec.args, **argspec.kwargs)

            # Add the arguments to the command's parser
            self._set_up_args(cmd)

        # Use the function description, not the __main__ docstring, if only one command
        if only_one_cmd:
            self._parsers["__root__"].description = next(iter(self._commands.values())).description

        # Make the magic happen
        parsed_args = vars(root_parser.parse_args())

        # Resolve the command that needs to be called
        if only_one_cmd:
            cmd = next(iter(self._commands.values()))
            self._current_parser = self._parsers["__root__"]
        else:
            # Find the actual command we need to execute by traversing the subparser tree. Call each stop along the way.
            path = "__root__"
            while path in self._subparsers:
                # Find the variable name for this subparser's command metavar and read the value. If it's none, run the
                # current stop of our path in the tree.
                subcmd_metavar = self._commands[path].get_subcommand_metavar(self._options.command_metavar)
                subcmd_name = parsed_args[subcmd_metavar]
                if subcmd_name is None:
                    break

                # Resolve any command aliases
                if subcmd_name in self._command_aliases:
                    subcmd_name = self._command_aliases[subcmd_name]

                self._is_calling_target = False
                self._current_parser = self._parsers[path]
                self._commands[path].call(parsed_args)

                # Update the path and continue
                if path == "__root__":
                    path = subcmd_name
                else:
                    path += f" {subcmd_name}"

            # If the command is unknown, print the help for the most recent parent
            if path not in self._commands:
                self._parsers[path.rsplit(" ", 1)[0]].print_help(file=self._options.output)
                return None
            if path == "__root__" and self._commands["__root__"].function.__name__ == "<lambda>":
                root_parser.print_help(file=self._options.output)
                return None

            # Found command
            self._current_parser = self._parsers[path]
            cmd = self._commands[path]

        self._is_calling_target = True
        result = cmd.call(parsed_args)
        self._current_parser = None
        return result

    def _build_subtype(
        self, parent_func_arg_name: str, subtype_info: SubtypeDecoratorInfo, build_kwargs: Dict[str, Any]
    ) -> Any:
        type_ = subtype_info.type_
        factory = subtype_info.factory or type_.__call__
        template = subtype_info.factory or type_.__init__  # type: ignore[misc]
        hints = get_type_hints(template, include_extras=True)
        normalized_kwargs: Dict[str, Any] = dict()

        params: Dict[str, inspect.Parameter] = {
            k: v
            for k, v in inspect.signature(template).parameters.items()
            if (v.kind != v.VAR_POSITIONAL) and (v.kind != v.VAR_KEYWORD)
        }

        missing_required_keys = [
            normalize_name(n)
            for i, (n, p) in enumerate(params.items())
            if (n not in build_kwargs) and (i != 0 or p.name != "self")
        ]
        if len(missing_required_keys) > 0:
            missing_specs = list()
            for key in missing_required_keys:
                arg_value_type, modifiers = CommandArg.normalize_type(type_.__name__, params[key], hints)
                missing_specs.append(f"{key} ({arg_value_type.__name__})")
            self.error(f"the following keys are required for {parent_func_arg_name}: {', '.join(missing_specs)}")

        # Iterate over all parameters
        for func_arg_name, param in params.items():
            try:
                func_arg_name = normalize_name(func_arg_name)
                if func_arg_name == "self":
                    continue
                param_value = build_kwargs[func_arg_name]
                del build_kwargs[func_arg_name]
                arg_value_type, modifiers = CommandArg.normalize_type(type_.__name__, param, hints)
            except ArguablyException:
                raise ArguablyException(f"Error processing parameter {func_arg_name} of subtype {type_.__name__}")
            if len(modifiers) > 0:
                raise ArguablyException(
                    f"Error processing parameter {func_arg_name} of subtype {type_.__name__}: Cannot use modifiers "
                    f"on subtypes"
                )
            normalized_kwargs[func_arg_name] = arg_value_type(param_value)

        # The calls to .error() cause an exit
        if len(build_kwargs) > 1:
            self.error(f"unexpected keys for {parent_func_arg_name}: {', '.join(build_kwargs)}")
        elif len(build_kwargs) > 0:
            self.error(f"unexpected key for {parent_func_arg_name}: {next(iter(build_kwargs))}")

        return factory(**normalized_kwargs)

    def resolve_subtype(
        self, func_arg_name: str, arg_value_type: type, subtype_: Optional[str], build_kwargs: Dict[str, Any]
    ) -> Any:
        options = self.find_subtype(arg_value_type)
        if len(options) == 0:
            options = [SubtypeDecoratorInfo(arg_value_type)]
        if len(options) == 1:
            return self._build_subtype(func_arg_name, options[0], build_kwargs)
        matches = [op for op in options if op.alias == subtype_]
        if len(matches) == 0:
            self.error(f"unknown subtype `{subtype_}` for {func_arg_name}")
        if len(matches) > 1:
            raise ArguablyException(f"More than one match for subtype `{subtype_}` of type {arg_value_type}")
        return self._build_subtype(func_arg_name, matches[0], build_kwargs)


context = _Context()


########################################################################################################################
# Exposed for API


run = context.run
is_target = context.is_target
error = context.error


def command(
    func: Optional[Callable] = None,
    /,
    *,
    # Arguments below are passed through to `CommandDecoratorInfo`
    alias: Optional[str] = None,
    help: bool = True,
) -> Callable:
    """
    Mark a function as a command that should appear on the CLI. If multiple functions are decorated with this, they will
    all be available as subcommands. If only one function is decorated, it is automatically selected - no need to
    specify it on the CLI.

    Args:
        func: The target function.
        alias: An alias for this function. For example, `@arguably.command(alias="h")` would alias `h` to the function
            that follows.
        help: If `False`, the help flag `-h/--help` will not automatically be added to this function.

    Returns:
        If called with parens `@arguably.command(...)`, returns the decorated function. If called without parens
            `@arguably.command`, returns the function `wrap(func_)`, which returns `func_`.

    Examples:
        ```python
        #!/usr/bin/env python3
        import arguably

        @arguably.command
        def some_function(required, not_required=2, *others: int, option: float = 3.14):
            \"\"\"
            this function is on the command line!

            Args:
                required: a required parameter
                not_required: this one isn't required, since it has a default
                *others: all the other positional arguments go here
                option: [-x] an option, short name is in brackets
            \"\"\"

        if __name__ == "__main__":
            arguably.run()
        ```

        ```console
        user@machine:~$ python3 readme-1.py -h
        usage: readme-1.py [-h] [-x OPTION] required [not-required] [others ...]

        this function is on the command line!

        positional arguments:
          required             a required parameter (type: str)
          not-required         this one isn't required, since it has a default (type: int, default: 2)
          others               all the other positional arguments go here (type: int)

        options:
          -h, --help           show this help message and exit
          -x, --option OPTION  an option, short name is in brackets (type: float, default: 3.14)
        ```

        Or, with multiple commands:

        ```python
        #!/usr/bin/env python3
        import arguably

        @arguably.command(alias="f")
        def first(): ...

        @arguably.command(alias="s")
        def second(): ...

        @arguably.command
        def second__subcmd1(): ...

        def second__subcmd2(): ...
        arguably.command(second__subcmd2)  # Can also be invoked this way

        if __name__ == "__main__":
            arguably.run()
        ```

        ```console
        user@machine:~$ python3 command.py -h
        usage: command-example-2.py [-h] command ...

        positional arguments:
          command
            first (f)
            second (s)

        options:
          -h, --help    show this help message and exit
        ```

        ```console
        user@machine:~$ python3 command.py s -h
        usage: command-example-2.py second [-h] command ...

        positional arguments:
          command
            subcmd1
            subcmd2

        options:
          -h, --help  show this help message and exit
        ```
    """

    def wrap(func_: Callable) -> Callable:
        context.add_command(function=func_, alias=alias, help=help)
        return func_

    # Handle being called as either @arguably.command or @arguably.command()
    # We have type: ignore due to https://github.com/python/mypy/issues/10740
    return wrap if func is None else wrap(func)  # type: ignore[return-value]


def subtype(
    cls: Optional[type] = None,
    /,
    *,
    # Arguments below are passed through to `SubtypeDecoratorInfo`
    alias: str,
) -> Union[Callable[[type], type], type]:
    """
    Mark a decorated class as a subtype that should be buildable for a parameter using arg.builder(). The alias
    parameter is required.

    Args:
        cls: The target class.
        alias: An alias for this class. For example, `@arguably.subtype(alias="foo")` would cause this class to be built
            any time an applicable arg is given a string starting with `foo,...`

    Returns:
        If called with parens `@arguably.subtype(...)`, returns the decorated class. If called without parens
            `@arguably.subtype`, returns the function `wrap(cls_)`, which returns `cls_`.

    Examples:
        ```python
        import arguably
        from dataclasses import dataclass
        from typing import Annotated

        class Nic: ...

        @arguably.subtype(alias="tap")
        @dataclass
        class TapNic(Nic):
            model: str

        @dataclass
        class UserNic(Nic):
            hostfwd: str

        arguably.subtype(UserNic, alias="user")  # Can also be called like this

        @arguably.command
        def qemu_style(*, nic: Annotated[list[Nic], arguably.arg.builder()]):
            print(f"{nic=}")

        if __name__ == "__main__":
            arguably.run()
        ```

        ```console
        user@machine:~$ python3 subtype.py --nic tap,model=e1000 --nic user,hostfwd=tcp::10022-:22
        nic=[TapNic(model='e1000'), UserNic(hostfwd='tcp::10022-:22')]
        ```
    """

    def wrap(cls_: type) -> type:
        if not isinstance(cls_, type):
            raise ArguablyException(
                f"Decorated value {cls_} is not a type, which is required for `@arguably.subtype()`"
            )
        context.add_subtype(type_=cls_, alias=alias)
        return cls_

    # Handle being called as either @arguably.subtype or @arguably.subtype()
    return wrap if cls is None else wrap(cls)
