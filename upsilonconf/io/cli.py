from argparse import ArgumentParser
from pathlib import Path
from typing import Tuple, Any, Sequence

from .base import ConfigIO
from ..config import Configuration


class ConfigParser:
    """
    Wrapper around ArgumentParser with a configuration group.

    This wrapper adds a *configuration* group to an argument parser.
    With this group, positional arguments are parsed as key-value pairs.
    Additionally, a ``--config`` option is added if an IO has been specified.
    The ``--config`` option takes a filename as argument
    from which a base configuration can be loaded.
    """

    @staticmethod
    def _assignment_expr(s: str) -> Tuple[str, Any]:
        """Parse assignment expression argument."""
        import json

        key, val = s.split("=", maxsplit=1)
        try:
            val = json.loads(val)
        except json.JSONDecodeError:
            pass

        return key, val

    def __init__(
        self,
        parser: ArgumentParser = None,
        config_io: ConfigIO = None,
        return_ns: bool = None,
    ):
        """
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
        if return_ns is None:
            return_ns = parser is not None

        self._parser = ArgumentParser() if parser is None else parser
        self._config_io = config_io
        self.return_ns = return_ns

        self._modify_parser()

    def _modify_parser(self):
        """Add the configuration group to the parser."""
        group = self._parser.add_argument_group("configuration")
        group.add_argument(
            "overrides",
            nargs="*",
            type=self._assignment_expr,
            help="configuration options to override in the config file",
            metavar="KEY=VALUE",
        )

        if self._config_io is not None:
            group.add_argument(
                "--config",
                type=Path,
                help="path to configuration file",
                metavar="FILE",
                dest="config",
            )

    @property
    def parser(self) -> ArgumentParser:
        """Wrapped `ArgumentParser` instance."""
        return self._parser

    def parse_config(self, args: Sequence[str] = None):
        """
        Parse a configuration from command line arguments.

        Parameters
        ----------
        args : sequence of str, optional
            The list of arguments to parse.
            By default, arguments are taken from ``sys.argv``.

        Returns
        -------
        config : Configuration
            The configuration as specified by the command line arguments.
        ns : Namespace, optional
            The namespace with non-configuration arguments.
            This is only returned if `return_ns` is ``True``.
        """
        ns = self._parser.parse_args(args)
        config = (
            Configuration()
            if self._config_io is None or ns.config is None
            else self._config_io.load_config(ns.config)
        )
        config.overwrite_all(ns.overrides)
        if not self.return_ns:
            return config

        del ns.overrides
        if self._config_io is not None:
            del ns.config

        return config, ns
