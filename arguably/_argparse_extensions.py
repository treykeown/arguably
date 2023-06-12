from __future__ import annotations

import argparse
import enum
import sys
from gettext import gettext
from typing import (
    Callable,
    cast,
    Any,
    TextIO,
    IO,
    Sequence,
    Union,
    Optional,
    List,
    Dict,
    Tuple,
)

import arguably._context as ctx
import arguably._modifiers as mods
import arguably._util as util


def normalize_action_input(values: Union[str, Sequence[Any], None]) -> List[str]:
    """Normalize `values` input to be a list"""
    if values is None:
        return list()
    elif isinstance(values, str):
        # "-" means empty
        return list() if values == "-" else [values]
    else:
        return list(values)


class HelpFormatter(argparse.HelpFormatter):
    """HelpFormatter modified for arguably"""

    def add_argument(self, action: argparse.Action) -> None:
        """
        Corrects _max_action_length for the indenting of subparsers, see https://stackoverflow.com/questions/32888815/
        """
        if action.help is not argparse.SUPPRESS:
            # find all invocations
            get_invocation = self._format_action_invocation
            invocations = [get_invocation(action)]
            current_indent = self._current_indent
            for subaction in self._iter_indented_subactions(action):
                # compensate for the indent that will be added
                indent_chg = self._current_indent - current_indent
                added_indent = "x" * indent_chg
                invocations.append(added_indent + get_invocation(subaction))

            # update the maximum item length
            invocation_length = max([len(s) for s in invocations])
            action_length = invocation_length + self._current_indent
            self._action_max_length = max(self._action_max_length, action_length)

            # add the item to the list
            self._add_item(self._format_action, [action])

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Changes metavar printing for parameters, only displays it once"""
        if not action.option_strings or action.nargs == 0:
            # noinspection PyProtectedMember
            return super()._format_action_invocation(action)
        default_metavar = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default_metavar)
        return ", ".join(action.option_strings) + " " + args_string

    def _metavar_formatter(
        self,
        action: argparse.Action,
        default_metavar: str,
    ) -> Callable[[int], Tuple[str, ...]]:
        """Mostly copied from the original _metavar_formatter, but special-cases enum member printing"""
        if action.metavar is not None:
            result = action.metavar
        elif action.choices is not None:
            if isinstance(next(iter(action.choices)), enum.Enum):
                choice_strs = [choice.name for choice in action.choices]
            else:
                choice_strs = [str(choice) for choice in action.choices]
            result = "{%s}" % ",".join(choice_strs)
        else:
            result = default_metavar

        def _format(tuple_size: int) -> Tuple[str, ...]:
            if isinstance(result, tuple):
                return result
            else:
                return (result,) * tuple_size

        return _format

    def _split_lines(self, text: str, width: int) -> List[str]:
        """Copied from the original _split_lines, but we don't replace multiple spaces with only one"""
        # text = self._whitespace_matcher.sub(' ', text).strip()
        # The textwrap module is used only for formatting help.
        # Delay its import for speeding up the common usage of argparse.
        import textwrap

        return textwrap.wrap(text, width)

    def _format_args(self, action: argparse.Action, default_metavar: str) -> str:
        """Same as stock, but backport ZERO_OR_MORE behavior for 3.8"""
        get_metavar = self._metavar_formatter(action, default_metavar)
        if action.nargs is None:
            result = "%s" % get_metavar(1)
        elif action.nargs == argparse.OPTIONAL:
            result = "[%s]" % get_metavar(1)
        elif action.nargs == argparse.ZERO_OR_MORE:
            metavar = get_metavar(1)
            if len(metavar) == 2:
                result = "[%s [%s ...]]" % metavar
            else:
                result = "[%s ...]" % metavar
        elif action.nargs == argparse.ONE_OR_MORE:
            result = "%s [%s ...]" % get_metavar(2)
        elif action.nargs == argparse.REMAINDER:
            result = "..."
        elif action.nargs == argparse.PARSER:
            result = "%s ..." % get_metavar(1)
        elif action.nargs == argparse.SUPPRESS:
            result = ""
        else:
            try:
                formats = ["%s" for _ in range(action.nargs)]  # type: ignore[arg-type]
            except TypeError:
                raise ValueError("invalid nargs value") from None
            result = " ".join(formats) % get_metavar(action.nargs)  # type: ignore[arg-type]
        return result


class ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser modified for arguably"""

    def __init__(self, *args: Any, output: Optional[TextIO] = None, **kwargs: Any):
        """Adds output redirection capabilites"""
        super().__init__(*args, **kwargs)
        self._output = output

    def _print_message(self, message: str, file: Optional[IO[str]] = None) -> None:
        """Allows redirecting all prints"""
        if message:
            # argparse.ArgumentParser defaults to sys.stderr in this function, though most seems to go to stdout
            file = self._output or file or sys.stderr
            file.write(message)

    def _get_value(self, action: argparse.Action, arg_string: str) -> Any:
        """Mostly copied from the original _get_value, but prints choices on failure"""
        type_func = self._registry_get("type", action.type, action.type)
        if not callable(type_func):
            msg = gettext("%r is not callable")
            raise argparse.ArgumentError(action, msg % type_func)

        try:
            if isinstance(type_func, type) and issubclass(type_func, enum.Enum):
                mapping = ctx.context.get_enum_mapping(type_func)
                if arg_string not in mapping:
                    raise ValueError(arg_string)
                result = mapping[arg_string]
            else:
                result = cast(Callable, type_func)(arg_string)
        except argparse.ArgumentTypeError as err:
            msg = str(err)
            raise argparse.ArgumentError(action, msg)
        except (TypeError, ValueError):
            name = getattr(action.type, "__name__", repr(action.type))
            # Added code is here
            if action.choices is not None:
                choice_strs = [
                    util.normalize_name(c.name, spaces=False) if isinstance(c, enum.Enum) else str(c)
                    for c in action.choices
                ]
                args = {"type": name, "value": arg_string, "choices": ", ".join(repr(c) for c in choice_strs)}
                msg = gettext("invalid choice: %(value)r (choose from %(choices)s)")
            else:
                args = {"type": name, "value": arg_string}
                msg = gettext("invalid %(type)s value: %(value)r")
            raise argparse.ArgumentError(action, msg % args)

        return result

    def _check_value(self, action: argparse.Action, value: Any) -> None:
        """'Just trust me' for enums, otherwise default behavior"""
        type_func = self._registry_get("type", action.type, action.type)
        if isinstance(type_func, type) and issubclass(type_func, enum.Enum):
            return

        # converted value must be one of the choices (if specified)
        if action.choices is not None and value not in action.choices:
            args = {
                "value": value,
                "choices": ", ".join(
                    [
                        util.normalize_name(c.name, spaces=False) if isinstance(c, enum.Enum) else repr(c)
                        for c in action.choices
                    ]
                ),
            }
            msg = gettext("invalid choice: %(value)r (choose from %(choices)s)")
            raise argparse.ArgumentError(action, msg % args)


class ListTupleBuilderAction(argparse.Action):
    """
    Special action for arguably - handles lists, tuples, and builders. Designed to handle:
        * lists - List[int], List[str]
        * tuples - Tuple[int, int, int], Tuple[str, float, int]
        * builders - Annotated[FooClass, arguably.arg.builder()]
        * list of tuples - List[Tuple[int, int]]
        * list of builders - Annotated[List[FooClass], arguably.arg.builder()]
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._command_arg = kwargs["command_arg"]
        del kwargs["command_arg"]

        super().__init__(*args, **kwargs)

        # Check if we're handling a list
        self._is_list = any(isinstance(m, mods.ListModifier) for m in self._command_arg.modifiers)

        # Check if we're handling a tuple (or a list of tuples)
        self._is_tuple = any(isinstance(m, mods.TupleModifier) for m in self._command_arg.modifiers)

        # Check if we're handling a builder (or a list of builders)
        self._is_builder = any(isinstance(m, mods.BuilderModifier) for m in self._command_arg.modifiers)

        if self._is_tuple and self._is_builder:
            raise util.ArguablyException(f"{'/'.join(self.option_strings)} cannot use both tuple and builder")

        # Validate that type is callable
        check_type_list = self.type if isinstance(self.type, list) else [self.type]
        for type_ in check_type_list:
            if not callable(type_):
                type_name = f"{self.type}" if not isinstance(self.type, list) else f"{type_} in {self.type}"
                raise util.ArguablyException(f"{'/'.join(self.option_strings)} type {type_name} is not callable")

        # Keep track of the real type and real nargs, lie to argparse to take in a single (comma-separated) string
        assert isinstance(self.type, type) or isinstance(self.type, list)
        self._real_type: Union[type, List[type]] = self.type
        self.type = str

        # Make metavar comma-separated as well
        if isinstance(self.metavar, tuple):
            self.metavar = ",".join(self.metavar)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        value_strs: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None,
    ) -> None:
        value_strs = normalize_action_input(value_strs)

        # Split values and convert to self._real_type
        values = list()
        for value_str in value_strs:
            split_value_str = [util.unwrap_quotes(v) for v in util.split_unquoted(value_str, delimeter=",")]
            if self._is_tuple:
                assert isinstance(self._real_type, list)
                if len(split_value_str) != len(self._real_type):
                    raise argparse.ArgumentError(self, f"expected {len(self._real_type)} values")
                value = tuple(type_(str_) for str_, type_ in zip(split_value_str, self._real_type))
                values.append(value)
            elif self._is_builder:
                values.append(self._build_from_str_values(parser, option_string, split_value_str))
            else:
                assert self._is_list
                assert isinstance(self._real_type, type)
                values.extend(self._real_type(str_) for str_ in split_value_str)

        # Set namespace variable
        if self._is_list:
            items = getattr(namespace, self.dest, list())
            items = argparse._copy_items(items)  # type: ignore[attr-defined]
            items.extend(values)
            setattr(namespace, self.dest, items)
        else:
            assert len(values) == 1
            setattr(namespace, self.dest, values[0])

    def _build_from_str_values(
        self,
        parser: argparse.ArgumentParser,
        option_string: Optional[str],
        split_value_str: List[str],
    ) -> Any:
        """
        Builds a class from the passed-in strings. Example:
            split_value_str=['foo', 'bar=123', 'bat=asdf'] -> FooClass(bar=123, bat='asdf')
        """

        # Separate out subtype and kwargs
        kwargs: Dict[str, Any] = dict()
        subtype_ = None
        if len(split_value_str) > 0 and "=" not in split_value_str[0]:
            subtype_ = split_value_str[0]
            kwarg_strs = split_value_str[1:]
        else:
            kwarg_strs = split_value_str

        # Build kwargs dict
        for kwarg_str in kwarg_strs:
            key, eq, value = kwarg_str.partition("=")
            if len(eq) == 0:
                raise argparse.ArgumentError(
                    self, f"type arguments should be of form key=value, {value} does not match"
                )
            if key in kwargs:
                if not isinstance(kwargs[key], list):
                    kwargs[key] = [kwargs[key], value]
                else:
                    kwargs[key].append(value)
            else:
                kwargs[key] = value

        # Set the value in the namespace to be a `_BuildTypeSpec`, which will be consumed later to build the class
        option_name = "" if option_string is None else option_string.lstrip("-")
        with ctx.context.current_parser(parser):
            assert isinstance(self._real_type, type)
            return ctx.context.resolve_subtype(option_name, self._real_type, subtype_, kwargs)


class FlagAction(argparse.Action):
    """Special action for arguably - handles `enum.Flag`. Clears default value and ORs together flag values."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None,
    ) -> None:
        flag_info = cast(util.EnumFlagInfo, self.const)
        value = flag_info.value

        if ctx.context.check_and_set_enum_flag_default_status(parser, flag_info.cli_arg_name):
            value |= getattr(namespace, flag_info.cli_arg_name)
        setattr(namespace, flag_info.cli_arg_name, value)
