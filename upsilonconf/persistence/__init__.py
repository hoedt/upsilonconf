from pathlib import Path
from typing import Union, TextIO, Any

from upsilonconf._utils import optional_dependency_to
from upsilonconf.config import Configuration


def _json_load(fp: TextIO) -> Any:
    """Wrapper around a library function for reading JSON files."""
    from json import load

    return load(fp)


def _json_dump(obj: Any, fp: TextIO, indent: int = 2, sort_keys: bool = False):
    """Wrapper around a library function for writing JSON files."""
    from json import dump

    dump(
        obj, fp, default=lambda o: o.__getstate__(), indent=indent, sort_keys=sort_keys
    )


@optional_dependency_to("read YAML files", "pyyaml")
def _yaml_load(fp: TextIO) -> Any:
    """Wrapper around a library function for reading YAML files."""
    from upsilonconf.persistence._yaml import load

    return load(fp)


@optional_dependency_to("write YAML files", "pyyaml")
def _yaml_dump(obj: Any, fp: TextIO, indent: int = 2, sort_keys: bool = False):
    """Wrapper around a library function for writing YAML files."""
    from upsilonconf.persistence._yaml import dump

    dump(obj, fp, indent=indent, sort_keys=sort_keys)


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
    ext = path.suffix.lower()
    if ext == ".json":
        _load = _json_load
    elif ext == ".yaml":
        _load = _yaml_load
    else:
        raise ValueError(f"unknown config file extension: '{ext}'")

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
    ext = path.suffix.lower()
    if ext == ".json":
        _dump = _json_dump
    elif ext == ".yaml":
        _dump = _yaml_dump
    else:
        raise ValueError(f"unknown config file extension: '{ext}'")

    with open(path, "r") as fp:
        _dump(config, fp)
