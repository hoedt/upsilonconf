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
        self._encoder = None
        self._encode_kwargs = {
            "indent": indent,
            "sort_keys": sort_keys,
        }

    @property
    def _json_encoder(self):
        if self._encoder is not None:
            return self._encoder

        from json import JSONEncoder

        class PatchedJSONEncoder(JSONEncoder):
            def default(self, o):
                try:
                    return dict(**o)
                except TypeError:
                    pass

                return JSONEncoder.default(self, o)

        self._encoder = PatchedJSONEncoder(**self._encode_kwargs)
        return self._encoder

    @property
    def extensions(self):
        return [".json"]

    def read_from(self, stream):
        from json import load

        return load(stream)

    def write_to(self, stream, conf):
        stream.writelines(self._json_encoder.iterencode(conf))
