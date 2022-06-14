import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Union, TextIO, Any, Sequence, overload

from upsilonconf.utils import optional_dependency_to
from upsilonconf.config import Configuration


__all__ = ["from_cli", "load", "save"] + [
    "_".join([fmt, kind]) for fmt in ("json", "yaml") for kind in ("load", "dump")
]


def json_load(fp: TextIO) -> Any:
    """Wrapper around a library function for reading JSON files."""
    from json import load

    return load(fp)


def json_dump(obj: Any, fp: TextIO, indent: int = 2, sort_keys: bool = False):
    """Wrapper around a library function for writing JSON files."""
    from json import dump

    dump(
        obj, fp, default=lambda o: o.__getstate__(), indent=indent, sort_keys=sort_keys
    )


@optional_dependency_to("read YAML files", "pyyaml")
def yaml_load(fp: TextIO) -> Any:
    """Wrapper around a library function for reading YAML files."""
    from upsilonconf.utils._yaml import load

    return load(fp)


@optional_dependency_to("write YAML files", "pyyaml")
def yaml_dump(obj: Any, fp: TextIO, indent: int = 2, sort_keys: bool = False):
    """Wrapper around a library function for writing YAML files."""
    from upsilonconf.utils._yaml import dump

    dump(obj, fp, indent=indent, sort_keys=sort_keys)


def _deduct_io_functions(path: Path):
    """
    Retrieve IO functions to read/write config files at a given path.

    Parameters
    ----------
    path: Path
        Path to deduct the correct IO functions from.

    Returns
    -------
    load : callable
        Function for reading config files at path.
    dump : callable
        Function for writing config files at path.
    """
    if path.is_dir():
        raise ValueError("The path can not be a directory")

    ext = path.suffix.lower()
    if ext == ".json":
        return json_load, json_dump
    elif ext == ".yaml":
        return yaml_load, yaml_dump
    else:
        raise ValueError(f"unknown config file extension: '{ext}'")


def load(path: Union[Path, str]) -> Configuration:
    """
    Read configuration from a file.

    Parameters
    ----------
    path : Path or str
        The path to the file to read the configuration from.

    Returns
    -------
    config: Configuration
        A configuration object with the values as provided in the file.
    """
    path = Path(path).expanduser().resolve()
    _load, _ = _deduct_io_functions(path)

    with open(path, "r") as fp:
        data = _load(fp)

    return Configuration(**data)


def save(config: Configuration, path: Union[Path, str]) -> None:
    """
    Write configuration to a file.

    Parameters
    ----------
    config : Configuration
        The configuration object to write to a file.
    path : Path or str
        The path to the file where the configuration is written to.
    """
    path = Path(path).expanduser().resolve()
    _, _dump = _deduct_io_functions(path)

    with open(path, "w") as fp:
        _dump(config, fp)


def assignment_expr(s: str):
    """Parse assignment expression argument."""
    key, val = s.split("=", maxsplit=1)
    try:
        val = json.loads(val)
    except json.JSONDecodeError:
        pass

    return key, val


def from_cli(args: Sequence[str] = None, parser: ArgumentParser = None):
    """
    Construct a configuration from a Command Line Interface.

    This function adds a `configuration` group to an argument parser
    and adds two extra options to the parser: `overrides` and `--config`.
    The `--config` flag allows to specify a config file to read a basic config from.
    The `overrides` option allows to specify one or more key value pairs
    that will overwrite any config values from the specified config file.

    Parameters
    ----------
    args : sequence of str, optional
        The list of arguments to parse.
        If not specified, they are taken from `sys.argv`.
    parser : ArgumentParser, optional
        The CLI parser to use as a base for retrieving configuration options.
        The parser can not (already) expect a variable number of positional args.
        Moreover, the parser should not already use the names `config` or `overrides`.
        If not specified, an empty parser will be created.

    Returns
    -------
    config : Configuration
        The configuration as specified by the command line arguments.
    """
    _parser = ArgumentParser() if parser is None else parser

    group = _parser.add_argument_group("configuration")
    group.add_argument(
        "--config",
        type=Path,
        help="path to configuration file",
        metavar="FILE",
        dest="config",
    )
    group.add_argument(
        "overrides",
        nargs="*",
        type=assignment_expr,
        help="configuration options to override in the config file",
        metavar="KEY=VALUE",
    )

    ns = _parser.parse_args(args)
    config = Configuration() if ns.config is None else load(ns.config)
    config.overwrite_all(ns.overrides)
    if parser is None:
        return config

    del ns.config
    del ns.overrides
    return config, ns
