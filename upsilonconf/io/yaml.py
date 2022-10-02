from collections.abc import Mapping

from ._optional_dependencies import optional_dependency_to
from .base import ConfigIO


class YAMLIO(ConfigIO):
    """IO for reading/writing YAML files."""

    def __init__(self, indent: int = 2, sort_keys: bool = False):
        """
        Parameters
        ----------
        indent : int, optional
            The number of spaces to use for indentation in the output file.
        sort_keys : bool, optional
            Whether keys should be sorted before writing to the output file.
        """
        self.kwargs = {"indent": indent, "sort_keys": sort_keys}
        self._loader = None
        self._dumper = None

    @property
    def _yaml_loader(self):
        """Lazily loaded (and patched) YAML loader."""
        if self._loader is not None:
            return self._loader

        import yaml
        import re

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
        self._loader = yaml.SafeLoader
        return self._loader

    @property
    def _yaml_dumper(self):
        """Lazily loaded YAML dumper."""
        if self._dumper is not None:
            return self._dumper

        import yaml

        yaml.SafeDumper.add_multi_representer(Mapping, yaml.SafeDumper.represent_dict)
        self._dumper = yaml.SafeDumper
        return self._dumper

    @property
    def extensions(self):
        return [".yaml", ".yml"]

    @optional_dependency_to("read YAML files", package="pyyaml")
    def read_from(self, stream):
        from yaml import load

        return load(stream, Loader=self._yaml_loader)

    @optional_dependency_to("write YAML files", package="pyyaml")
    def write_to(self, stream, conf):
        from yaml import dump

        return dump(conf, stream, Dumper=self._yaml_dumper, **self.kwargs)
