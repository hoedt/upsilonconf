import warnings
from pathlib import Path
from io import StringIO
from argparse import ArgumentParser, Namespace
from typing import Tuple, Any, Sequence, Optional, Union, Mapping

from .base import ConfigIO

__all__ = ["ConfigParser"]


class ConfigParser:
    """
    Wrapper around ArgumentParser with a configuration group.

    This wrapper adds a *configuration* group to an argument parser.
    With this group, positional arguments are parsed as key-value pairs.
    Additionally, a ``--config`` option is added if an IO has been specified.
    The ``--config`` option takes a filename as argument
    from which a base configuration can be loaded.

    .. versionadded:: 0.5.0

    .. versionchanged:: 0.8.0
       Argument `config_io` is no longer optional.

    Parameters
    ----------
    config_io : ConfigIO
        Specifies how configuration files are read.
    parser : ArgumentParser, optional
        The CLI parser to use as a base for retrieving configuration options.
        The parser can not (already) expect a variable number of positional args.
        Moreover, the parser should not already use the names *config* or *overrides*.
        If not specified, an empty parser will be created.
    return_ns : bool, optional
        If ``True``, `parse_config` will also return the namespace.
        If ``False``, it will only return the configuration.
        By default, `return_ns` is set to ``True`` if `parser` is not ``None``.
    """

    def __init__(
        self,
        config_io: ConfigIO,
        parser: Optional[ArgumentParser] = None,
        return_ns: Optional[bool] = None,
    ):
        if return_ns is None:
            return_ns = parser is not None
        if parser is None:
            parser = ArgumentParser()

        self._config_io = config_io
        self._parser = parser
        self.return_ns = return_ns

        self._modify_parser()

    def _modify_parser(self) -> None:
        """Add the configuration group to the parser."""
        group = self._parser.add_argument_group("configuration")

        def key_value_pair(s: str) -> Tuple[str, Any]:
            """Parse simple assignment expression argument."""
            key, val = s.split("=", maxsplit=1)
            try:
                new_val = self._config_io.read_from(StringIO(val))
                return key, new_val
            except ValueError:
                pass

            return key, val

        group.add_argument(
            "overrides",
            nargs="*",
            type=key_value_pair,
            help="configuration options to override in the config file",
            metavar="KEY=VALUE",
        )
        group.add_argument(
            "--config",
            type=Path,
            default=None,
            help="path to configuration file",
            metavar="FILE",
            dest="config",
        )

    @property
    def parser(self) -> ArgumentParser:
        """Wrapped `ArgumentParser` instance."""
        return self._parser

    def parse_cli(
        self, args: Optional[Sequence[str]] = None
    ) -> Union[Mapping[str, Any], Tuple[Mapping[str, Any], Namespace]]:
        """
        Parse key-value mapping from command line arguments.

        .. versionadded:: 0.8.0

        Parameters
        ----------
        args : sequence of str, optional
            The list of arguments to parse.
            By default, arguments are taken from ``sys.argv``.

        Returns
        -------
        config : Mapping
            A dictionary representing the mapping provided via CLI.
        ns : Namespace, optional
            The namespace with non-configuration arguments.
            This is only returned if `return_ns` is ``True``.
        """
        ns = self._parser.parse_args(args)
        result = {} if ns.config is None else self._config_io.read(ns.config)
        result |= dict(ns.overrides)
        if not self.return_ns:
            return result

        del ns.overrides
        del ns.config
        return result, ns

    def parse_config(self, args: Optional[Sequence[str]] = None):
        """
        Parse a configuration from command line arguments.

        .. deprecated:: 0.8.0
            ConfigIO.parse_config will be replaced by ConfigurationBase.from_cli

        Parameters
        ----------
        args : sequence of str, optional
            The list of arguments to parse.
            By default, arguments are taken from ``sys.argv``.

        Returns
        -------
        config : ConfigurationBase
            The configuration as specified by the command line arguments.
        ns : Namespace, optional
            The namespace with non-configuration arguments.
            This is only returned if `return_ns` is ``True``.
        """
        from ..config import CarefulConfiguration

        warnings.warn(
            "ConfigParser.parse_config will be replaced by ConfigurationBase.from_cli",
            DeprecationWarning,
            stacklevel=2,
        )

        out = self.parse_cli(args)
        if not isinstance(out, tuple):
            return CarefulConfiguration.from_dict(out)

        return CarefulConfiguration.from_dict(out[0]), out[1]
