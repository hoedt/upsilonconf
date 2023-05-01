import sys
from collections.abc import Mapping

from upsilonconf.io._optional_dependencies import optional_dependency_to
from .base import ConfigIO


class TOMLIO(ConfigIO):
    """
    IO for reading/writing TOML files.

    .. versionadded:: 0.6.0
    """

    @property
    def extensions(self):
        return [".toml"]

    @optional_dependency_to("read TOML files for python <3.11")
    def read_from(self, stream):
        if sys.version_info >= (3, 11):
            from tomllib import loads
        else:
            from tomlkit import loads

        return loads(stream.read())

    @optional_dependency_to("write TOML files")
    def write_to(self, stream, conf):
        import tomlkit

        d = tomlkit.document()
        for k, v in conf.items():
            if isinstance(v, Mapping):
                v = dict(v)
            d.add(k, tomlkit.item(v))

        return stream.write(tomlkit.dumps(d))
