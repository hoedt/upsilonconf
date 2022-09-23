from pathlib import Path
from typing import Union, Any, Mapping, Callable, overload

from .config import Configuration
from ._import_tricks import optional_dependency_to


__all__ = ["load", "save"] + [
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


def load(
    path: Union[Path, str], key_modifiers: Mapping[str, str] = None
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
    return Configuration.from_dict(_load(path), key_modifiers)


def save(
    config: Configuration,
    path: Union[Path, str],
    key_modifiers: Mapping[str, str] = None,
) -> None:
    """
    Write configuration to a file or directory.

    Parameters
    ----------
    config : Configuration
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
    config = config.to_dict(key_modifiers)
    path.parent.mkdir(exist_ok=True, parents=True)
    return _save(config, path)
