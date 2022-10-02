from .base import ConfigIO


class JSONIO(ConfigIO):
    """IO for reading/writing JSON files."""

    def __init__(self, indent: int = 2, sort_keys: bool = False):
        """
        Parameters
        ----------
        indent : int, optional
            The number of spaces to use for indentation in the output file.
        sort_keys : bool, optional
            Whether keys should be sorted before writing to the output file.
        """
        self.kwargs = {
            "default": lambda o: o.__getstate__(),
            "indent": indent,
            "sort_keys": sort_keys,
        }

    @property
    def extensions(self):
        return [".json"]

    def read_from(self, stream):
        from json import load

        return load(stream)

    def write_to(self, stream, conf):
        from json import dump

        return dump(conf, stream, **self.kwargs)
