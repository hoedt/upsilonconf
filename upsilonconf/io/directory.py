from .base import ConfigIO
from ..config import Configuration


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

    >>> upsilonconf.load_config("examples/hparam")
    ... Configuration(foo=1, baz=Configuration(a=0.1, b=0.2), bar='hparam')
    """

    DEFAULT_NAME = "config"

    def __init__(self, config_io: ConfigIO, name: str = None):
        if name is None:
            name = self.DEFAULT_NAME
        if len(name.rsplit(".", maxsplit=1)) < 2:
            name += config_io.default_ext

        self.name = name
        self.config_io = config_io

    @property
    def default_ext(self):
        return self.config_io.default_ext

    def read_from(self, stream):
        raise TypeError("directory IO does not support streams")

    def read(self, path):
        try:
            name, _ = self.name.rsplit(".", maxsplit=1)
            base_path = next(path.glob(f"{name}.*"))
            base_conf = self.config_io.read(base_path)
        except StopIteration:
            base_path = None
            base_conf = Configuration()

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

    def write(self, conf, path):
        file_path = path / self.name
        path.mkdir(exist_ok=True)
        self.config_io.write(conf, file_path)

    def write_to(self, stream, config):
        raise TypeError("directory IO does not support streams")
