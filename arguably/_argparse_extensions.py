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


class CommaSeparatedTupleAction(argparse.Action):
    """Special action for arguably, handles comma-separated values for tuples"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Special handling if self.type is a list - it's a list of all the types for this tuple
        check_type_list = self.type if isinstance(self.type, list) else [self.type]
        for type_ in check_type_list:
            if not callable(type_):
                type_name = f"{self.type}" if not isinstance(self.type, list) else f"{type_} in {self.type}"
                raise util.ArguablyException(f"{'/'.join(self.option_strings)} type {type_name} is not callable")

        # Keep track of the real type and real nargs, lie to argparse to take in a single (comma-separated) string
        assert isinstance(self.type, list)
        self._real_type: List[type] = self.type
        self.type = str

        # Make metavar comma-separated as well
        if isinstance(self.metavar, tuple):
            self.metavar = ",".join(self.metavar)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None,
    ) -> None:
        values = normalize_action_input(values)
        if len(values) != 0:
            # Unlike list, a tuple can only be specified one time
            assert len(values) == 1

            # Split values and convert to self._real_type
            value = values[0]
            split_values = list()
            split_str_values = util.split_unquoted(value, delimeter=",")

            # We have a list of types for the tuple, convert each item accordingly
            for str_value, value_type in zip(split_str_values, self._real_type):
                split_values.append(value_type(str_value))
            values = split_values

        # Set namespace variable
        setattr(namespace, self.dest, values)


class CommaSeparatedListAction(argparse._ExtendAction):  # noqa
    """
    Special action for arguably, handles comma-separated values for lists. Can be specified multiple times. Based off
    the "extend" action.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not callable(self.type):
            raise util.ArguablyException(f"{'/'.join(self.option_strings)} type {self.type} is not callable")
        self._real_type = self.type
        self.type = None

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None,
    ) -> None:
        values = normalize_action_input(values)

        # Split values and convert to self._real_type
        split_values = list()
        for value in values:
            split_str_values = [util.unwrap_quotes(v) for v in util.split_unquoted(value, delimeter=",")]
            split_values.extend(list(map(self._real_type, split_str_values)))
        values = split_values

        # Check length and set namespace variable
        if len(values) == 0 and self.required:
            raise argparse.ArgumentError(self, "expected at least one argument")
        super().__call__(parser, namespace, values, option_string)


class BuildTypeAction(argparse.Action):
    """
    Special action for arguably, handles building a class with a complex signature for __init__, or when multiple
    subclasses can be chosen from.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        assert isinstance(self.type, type)
        self._real_type: type = self.type
        self.type = None

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None,
    ) -> None:
        values = normalize_action_input(values)

        # Split values
        split_values = list()
        for value in values:
            split_str_values = [util.unwrap_quotes(v) for v in util.split_unquoted(value, delimeter=",")]
            split_values.extend(split_str_values)
        values = split_values

        # Separate out subtype and kwargs
        kwargs: Dict[str, Any] = dict()
        subtype_ = None
        if len(values) > 0 and "=" not in values[0]:
            subtype_ = values[0]
            values = values[1:]

        # Build kwargs dict
        for value in values:
            key, eq, value = value.partition("=")
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
            built_class = ctx.context.resolve_subtype(option_name, self._real_type, subtype_, kwargs)

        setattr(namespace, self.dest, built_class)


class EnumFlagAction(argparse.Action):
    """
    Special action for arguably, handles `enum.Flag`. Needed to clear default value if set, and to OR values together
    """

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
