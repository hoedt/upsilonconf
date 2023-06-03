from pathlib import Path
from typing import Mapping, Union, Optional

from ..config import ConfigurationBase
from ._optional_dependencies import OptionalDependencyError
from .base import ConfigIO, ExtensionIO, FlexibleIO
from .json import JSONIO
from .yaml import YAMLIO
from .toml import TOMLIO
from .directory import DirectoryIO


__all__ = [
    "OptionalDependencyError",
    "ConfigIO",
    "ExtensionIO",
    "JSONIO",
    "YAMLIO",
    "TOMLIO",
    "DirectoryIO",
    "load_config",
    "save_config",
    "from_cli",
]

_default_io = None


def get_default_io(default_ext: Optional[str] = None) -> ConfigIO:
    """
    Get the default I/O setup.

    Parameters
    ----------
    default_ext : str, optional
        The extension to use as the default for reading/writing config files.
        If not specified, the default is chosen for you.

    Returns
    -------
    default_io : ConfigIO
        The default IO for reading and writing configuration files.

    Raises
    ------
    ValueError
        If there is no (known) IO for the value passed for `default_ext`.
    """
    global _default_io
    if _default_io is not None:
        return _default_io

    _default_io = ExtensionIO(JSONIO(), YAMLIO(), TOMLIO(), default_ext=default_ext)
    _default_io[""] = DirectoryIO(_default_io)
    return _default_io


def load_config(
    path: Union[Path, str],
    key_mods: Optional[Mapping[str, str]] = None,
    config_io: Optional[ConfigIO] = None,
) -> ConfigurationBase:
    """
    Load configuration from a file.

    Parameters
    ----------
    path : Path or str
        Path to a readable text file on disk.
    key_mods : dict, optional
        A dictionary mapping key substrings to replacement patterns.
        This allows to modify keys with invalid characters for config keys.
    config_io : ConfigIO, optional
        The IO to use for reading the file.
        If not specified, the default IO will be used.

    Returns
    -------
    config : ConfigurationBase
        A configuration object with the key-value pairs as provided in the file.

    See Also
    --------
    io.get_default_io : retrieve the default IO.
    io.ConfigIO.load_config : implementation of functionality.
    """
    if config_io is None:
        config_io = get_default_io()

    return config_io.load_config(path, key_mods)


def save_config(
    config: ConfigurationBase,
    path: Union[Path, str],
    key_mods: Optional[Mapping[str, str]] = None,
    config_io: Optional[ConfigIO] = None,
) -> None:
    """
    Write a configuration data to disk.

    Parameters
    ----------
    config : ConfigurationBase
        The configuration object to save.
    path : Path or str
        Path to a writeable text file on disk.
    key_mods : dict, optional
        A dictionary mapping key substrings to replacement patterns.
        This allows to modify keys with invalid characters for config keys.
    config_io : ConfigIO, optional
        The IO to use for writing the file.
        If not specified, the default IO will be used.

    See Also
    --------
    io.get_default_io : retrieve the default IO.
    io.ConfigIO.save_config : implementation of functionality.
    """
    if config_io is None:
        config_io = get_default_io()

    config_io.save_config(config, path, key_mods)


def from_cli(args=None, parser=None, config_io=None):
    """
    Construct a configuration from a Command Line Interface.

    This function adds a *configuration* group to an argument parser
    and adds two extra options to the parser: *overrides* and *--config*.
    The *--config* flag allows to specify a config file to read a basic config from.
    The *overrides* option allows to specify one or more key value pairs
    that will overwrite any config values from the specified config file.

    Parameters
    ----------
    args : sequence of str, optional
        The list of arguments to parse.
        If not specified, they are taken from ``sys.argv``.
    parser : ArgumentParser, optional
        The CLI parser to use as a base for retrieving configuration options.
        The parser can not (already) expect a variable number of positional args.
        Moreover, the parser should not already use the names *config* or *overrides*.
        If not specified, an empty parser will be created.
    config_io : ConfigIO
        The IO to use for reading config files that are passed as argument.

    Returns
    -------
    config : ConfigurationBase
        The configuration as specified by the command line arguments.
    ns : Namespace, optional
        The namespace with additional arguments from the command line arguments.
        This is only returned if `parser` is not ``None``
    """
    from .cli import ConfigParser

    if config_io is None:
        config_io = get_default_io()

    parser = ConfigParser(parser, config_io=config_io)
    return parser.parse_config(args)
