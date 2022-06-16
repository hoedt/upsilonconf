import re
from typing import TextIO, Any
from collections.abc import Mapping

import yaml

_yaml_float_tag = "tag:yaml.org,2002:float"
_missing_yaml_floats = r"""^[-+]?(
    [0-9][0-9_]*\.[0-9_]*(?:[eE][0-9]+)?
   |\.[0-9][0-9_]*(?:[eE][0-9]+)?
   |[0-9][0-9_]*[eE][-+]?[0-9]+
)$"""
yaml.SafeLoader.add_implicit_resolver(
    _yaml_float_tag,
    re.compile(_missing_yaml_floats, re.X),
    list("-+0123456789."),
)


def load(fp: TextIO) -> Any:
    """Wrapper around `yaml.safe_load` with patched float formatting."""
    return yaml.load(fp, Loader=yaml.SafeLoader)


yaml.SafeDumper.add_multi_representer(Mapping, yaml.SafeDumper.represent_dict)


def dump(data: Any, fp: TextIO, indent: int = 2, sort_keys: bool = False) -> None:
    """Wrapper around `yaml.safe_dump` with patch to allow Configuration objects."""
    yaml.dump(data, fp, Dumper=yaml.SafeDumper, indent=indent, sort_keys=sort_keys)
