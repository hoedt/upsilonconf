from typing import Optional

from .base import ConfigIO


class DirectoryIO(ConfigIO):
    """
    IO for reading/writing configs from a directory.

    A config directory can hold any combination of the following three elements:
     1. The base configuration file with the name ``config`` (e.g. ``config.json``)
     2. Config files/directories with sub-configs to be added to the base config.
        These sub-configs are directly added to the base config.
        The filename of this sub-config will be a new(!) key in the base config.
     3. Config files/directories with config options for the base config.
        These sub-configs provide one or more sub-config options
        for an existing(!) key in the base config.
        Therefore, the filename must match one of the keys in the base config.

    .. versionadded:: 0.5.0

    Parameters
    ----------
    config_io : ConfigIO
        The io to use to read/write files in each directory.
    main_file : str, optional
        The filename that specifies the main config file when reading
        or the filename for the file that is created when writing.

    Examples
    --------
    Consider a directory with structure::

        examples/hparam/
          config.yaml
          bar.yaml
          baz.yaml

    with file-contents::

        # config.yaml
        foo: 1
        bar: option1

        # bar.yaml
        option1: hparam
        option2: not hparam

        # baz.yaml
        a: 0.1
        b: 0.2

    When reading this directory, we end up with the following configuration:

    >>> upsilonconf.load_config("examples/hparam")  # doctest: +SKIP
    PlainConfiguration(foo=1, baz=PlainConfiguration(a=0.1, b=0.2), bar='hparam')
    """

    DEFAULT_NAME = "config"

    def __init__(self, config_io: ConfigIO, main_file: Optional[str] = None):
        if main_file is None:
            main_file = self.DEFAULT_NAME

        parts = main_file.rsplit(".", maxsplit=1)
        name, ext = parts[0], (None if len(parts) < 2 else f".{parts[1]}")
        if ext is not None and ext not in config_io.extensions:
            raise ValueError("unsupported extension for given IO")

        self._file_name = name
        self._file_ext = ext
        self.config_io = config_io

    @property
    def extensions(self):
        return [""]

    @property
    def file_name(self) -> str:
        ext = self.config_io.default_ext if self._file_ext is None else self._file_ext
        return self._file_name + ext

    def read_from(self, stream):
        cls_name = self.__class__.__name__
        raise TypeError(f"{cls_name} does not support reading from stream")

    def parse_value(self, val):
        return self.config_io.parse_value(val)

    def read(self, path, encoding="utf-8"):
        try:
            base_path = next(path.glob(f"{self._file_name}.*"))
            base_conf = self.config_io.read(base_path, encoding)
            if self._file_ext is None:
                self._file_ext = base_path.suffix
        except StopIteration:
            base_path = None
            base_conf = {}

        for sub in path.iterdir():
            if sub == base_path:
                continue

            key, sub_conf = sub.stem, self.config_io.read(sub)
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

    def write(self, conf, path, encoding="utf-8"):
        file_path = path / self.file_name
        path.mkdir(exist_ok=True)
        self.config_io.write(conf, file_path, encoding)

    def write_to(self, stream, config):
        cls_name = self.__class__.__name__
        raise TypeError(f"{cls_name} does not support writing to stream")
