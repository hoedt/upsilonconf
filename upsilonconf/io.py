import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Union, Any, Sequence, Mapping, Callable, overload, Tuple

from .config import Configuration
from ._optional_dependency import optional_dependency_to


__all__ = ["from_cli", "load", "save"] + [
    "_".join([kind, fmt])
    for kind in ("load", "save")
    for fmt in ("json", "yaml", "dir")
]

DEFAULT_NAME = "config.json"


def load_json(path: Path) -> Mapping[str, Any]:
    """
    Read config from a JSON file.

    Parameters
    ----------
    path : Path
        Path to a readable JSON file.

    Returns
    -------
    config: Mapping
        A mapping constructed from the data in the file.
    """
    from json import load

    with open(path, "r") as fp:
        return load(fp)


def save_json(
    conf: Mapping[str, Any], path: Path, indent: int = 2, sort_keys: bool = False
):
    """
    Write config to a JSON file.

    Parameters
    ----------
    conf : Mapping
        The configuration object to save.
    path : Path
        Path to a writeable JSON file.
    indent : int, optional
        The number of spaces to use for indentation in the output file.
    sort_keys : bool, optional
        Whether keys should be sorted before writing to the output file.
    """
    from json import dump

    kwargs = {
        "default": lambda o: o.__getstate__(),
        "indent": indent,
        "sort_keys": sort_keys,
    }

    with open(path, "w") as fp:
        dump(conf, fp, **kwargs)


@optional_dependency_to("read YAML files", "pyyaml")
def load_yaml(path: Path) -> Mapping[str, Any]:
    """
    Read config from a YAML file.

    Parameters
    ----------
    path : Path
        Path to a readable YAML file.

    Returns
    -------
    config: Mapping
        A mapping constructed from the data in the file.
    """
    from upsilonconf._yaml import load

    with open(path, "r") as fp:
        return load(fp)


@optional_dependency_to("write YAML files", "pyyaml")
def save_yaml(
    conf: Mapping[str, Any], path: Path, indent: int = 2, sort_keys: bool = False
):
    """
    Write config to a YAML file.

    Parameters
    ----------
    conf : Mapping
        The configuration object to save.
    path : Path
        Path to a writeable YAML file.
    indent : int, optional
        The number of spaces to use for indentation in the output file.
    sort_keys : bool, optional
        Whether keys should be sorted before writing to the output file.
    """
    from upsilonconf._yaml import dump

    with open(path, "w") as fp:
        dump(conf, fp, indent=indent, sort_keys=sort_keys)


def load_dir(path: Path) -> Mapping[str, Any]:
    """
    Read config from a directory.

    A config directory can hold any combination of the following three elements:
     1. The base configuration file with the name `config` (e.g. `config.json`)
     2. Config files/directories with sub-configs to be added to the base config.
        These sub-configs are directly added to the base config.
        The filename of this sub-config will be a new(!) key in the base config.
     3. Config files/directories with config options for the base config.
        These sub-configs provide one or more sub-config options
        for an existing(!) key in the base config.
        Therefore, the filename must match one of the keys in the base config.

    Parameters
    ----------
    path : Path
        Path to a readable directory with one or more configuration files.

    Returns
    -------
    config : Mapping
        The configuration represented by the directory at the given path.
    """
    try:
        base_path = next(path.glob("config.*"))
        base_conf = load(base_path)
    except StopIteration:
        base_path = None
        base_conf = Configuration()

    for sub in path.iterdir():
        if sub == base_path:
            continue

        key, sub_conf = sub.stem, load(sub)
        if key in base_conf:
            option = base_conf.pop(key)
            try:
                sub_conf = sub_conf[option]
            except (KeyError, TypeError):
                raise ValueError(
                    f"value corresponding to '{key}' in the base config "
                    f"does not match any of the options in '{sub.name}'"
                )

        base_conf[key] = sub_conf

    return base_conf


def save_dir(conf: Mapping[str, Any], path: Path, name: str = None) -> None:
    """
    Write config to a directory.

    Parameters
    ----------
    conf : Mapping
        The configuration object to save.
    path : Path
        Path to a writeable directory.
    name : str, optional
        The filename to use for the output config file
    """
    if name is None:
        name = DEFAULT_NAME

    file_path = path / name
    _save = _get_io_function(file_path, write=True)
    path.mkdir(exist_ok=True)
    _save(conf, file_path)


@overload
def _get_io_function(
    path: Path, write: bool = False
) -> Callable[[Path], Mapping[str, Any]]:
    ...


@overload
def _get_io_function(
    path: Path, write: bool = True
) -> Callable[[Mapping[str, Any], Path], None]:
    ...


def _get_io_function(path: Path, write: bool = False):
    """
    Retrieve IO functions to read/write config files at a given path.

    Parameters
    ----------
    path: Path
        Path to deduct the correct IO functions from.
    write: bool, optional
        Return function to write configs if `True`,
        otherwise a function for reading configs is returned.

    Returns
    -------
    io_func : Path -> Mapping
        Function for reading/writing config files from/to path.
    """
    ext = path.suffix.lower()
    if ext == "":
        return save_dir if write else load_dir
    if ext == ".json":
        return save_json if write else load_json
    elif ext == ".yaml":
        return save_yaml if write else load_yaml

    raise ValueError(f"unknown config file extension: '{ext}'")


def __replace_in_keys(
    mapping: Union[Mapping[str, Any], Any], s: str, r: str
) -> Union[Mapping[str, Any], Any]:
    """
    Take a mapping object and replace all occurrencies of `s` with `r` in any
    of its keys.

    This function is called recursively.

    Modelled after the Stack Overflow answer by Farhan Haider:
    https://stackoverflow.com/questions/21650850/pyyaml-replace-dash-in-keys-with-underscore#answer-55986782

    Parameters
    ----------
    mapping : Mapping
        The mapping object to be modified.
    s : str
        The string to be replaced in the keys.
    r : str
        The replacement string.

    Returns
    -------
        The dictionary with all strings `s` replaced with `r` in the keys.
    """
    # Traverse all the keys and replace `s` with `r`
    dictionary = {}
    for key, value in mapping.items():
        try:
            # Call this method recursively
            value = __replace_in_keys(value, s, r)
        except Exception:
            # `value` is not of the mapping type
            pass
        dictionary[key.replace(s, r)] = value

    return dictionary


def _replace_in_keys(
    config: Mapping[str, Any], key_modifiers: Mapping[str, str]
) -> Mapping[str, Any]:
    """
    Replace strings in the keys of a mapping object.

    Parameters
    ----------
    config : Mapping
        The configuration object (or dictionary) to be modified.
    key_modifiers : dict
        The dictionary with the replacements.

    Returns
    -------
    dict
        A dictionary with the modified keys.

    """
    _config = config
    # Replace longest strings first
    # - `sorted(..., reverse=True)` takes care of that
    for key in sorted(key_modifiers.keys(), key=lambda k: len(k), reverse=True):
        _config = __replace_in_keys(_config, key, key_modifiers[key])
    return _config


def load(
    path: Union[Path, str], key_modifiers: Mapping[str, str] = {}
) -> Configuration:
    """
    Read configuration from a file or directory.

    Parameters
    ----------
    path : Path or str
        Path to a readable file.
    key_modifiers : dict, optional
        A dictionary with replacement strings: The configuration keys will be
        modified, by replacing the string from the key_modifiers key with its
        value.

    Returns
    -------
    config : Configuration
        A configuration object with the values as provided in the file.
    """
    path = Path(path).expanduser().resolve()
    _load = _get_io_function(path, write=False)
    config = _replace_in_keys(_load(path), key_modifiers)
    return Configuration(**config)


def save(
    config: Mapping[str, Any],
    path: Union[Path, str],
    key_modifiers: Mapping[str, str] = {},
) -> None:
    """
    Write configuration to a file or directory.

    Parameters
    ----------
    config : Mapping
        The configuration object to save.
    path : Path or str
        Path to a writeable file.
    key_modifiers : dict, optional
        A dictionary with replacement strings: The configuration keys will be
        modified, by replacing the string from the key_modifiers key with its
        value.
    """
    path = Path(path).expanduser().resolve()
    _save = _get_io_function(path, write=True)
    path.parent.mkdir(exist_ok=True, parents=True)
    config = _replace_in_keys(config, key_modifiers)
    return _save(config, path)


def assignment_expr(s: str) -> Tuple[str, Any]:
    """Parse assignment expression argument."""
    key, val = s.split("=", maxsplit=1)
    try:
        val = json.loads(val)
    except json.JSONDecodeError:
        pass

    return key, val


@overload
def from_cli() -> Configuration:
    ...


@overload
def from_cli(args: Sequence[str]) -> Configuration:
    ...


@overload
def from_cli(
    args: Sequence[str], parser: ArgumentParser
) -> Tuple[Configuration, Namespace]:
    ...


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
    ns : Namespace
        The namespace with additional arguments from the command line arguments.
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
