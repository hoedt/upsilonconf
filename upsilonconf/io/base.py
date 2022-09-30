from abc import ABC, abstractmethod
from pathlib import Path
from typing import Mapping, Any, Union

from ..config import Configuration


class ConfigIO(ABC):
    """Interface for reading/writing configurations to/from files."""

    @abstractmethod
    def read(self, path: Path) -> Mapping[str, Any]:
        """
        Read from a configuration file.

        Parameters
        ----------
        path : Path
            Path to a readable configuration file.
        """
        ...

    @abstractmethod
    def write(self, conf: Mapping[str, Any], path: Path) -> None:
        """
        Write to a configuration file.

        Parameters
        ----------
        conf : Mapping
            The key-value pairs to save.
        path : Path
            Path to a writeable configuration file.
        """
        ...

    def load_config(
        self, path: Union[Path, str], key_mods: Mapping[str, str] = None
    ) -> Configuration:
        """
        Load configuration from disk.

        Parameters
        ----------
        path : Path or str
            Path to a readable location on disk.
        key_mods : dict, optional
            A dictionary with replacement strings: The configuration keys will be
            modified, by replacing the string from the key_modifiers key with its
            value.

        Returns
        -------
        config : Configuration
            A configuration object with the values as provided in the file.
        """
        path = Path(path).expanduser().resolve()
        m = self.read(path)
        return Configuration.from_dict(m, key_mods)

    def save_config(
        self,
        config: Configuration,
        path: Union[Path, str],
        key_mods: Mapping[str, str] = None,
    ) -> None:
        """
        Save configuration to disk.

        Parameters
        ----------
        config : Configuration
            The configuration object to save.
        path : Path or str
            Path to a writeable location on disk.
        key_mods : dict, optional
            A dictionary with replacement strings: The configuration keys will be
            modified, by replacing the string from the key_modifiers key with its
            value.
        """
        path = Path(path).expanduser().resolve()
        m = config.to_dict(key_mods)
        return self.write(m, path)


class FlexibleIO(ConfigIO):
    """
    IO for selecting IOs based on file extensions.

    This IO keeps a mapping from file extensions to their corresponding IOs.
    Whenever a file needs to be read/written, the file extension is used
    to retrieve the correct IO and forward the read/write operation.
    """

    def __init__(self, ext_io_map: Mapping[str, ConfigIO]):
        """
        Parameters
        ----------
        ext_io_map : Mapping[str, ConfigIO]
            A ``dict``-like object mapping extensions to the corresponding IO.
            The file extension should include the starting period (``.``).
        """
        self._ext_io_map = {}
        for ext, io in ext_io_map.items():
            self.update(ext, io)

    def _retrieve_io(self, path: Path) -> ConfigIO:
        """
        Retrieve IO to read/write config files given a path.

        Parameters
        ----------
        path: Path
            Path to infer the file format from.

        Returns
        -------
        config_io : ConfigIO
            Object for reading/writing config files from/to `path`.
        """
        ext = path.suffix.lower()
        try:
            config_io = self._ext_io_map[ext]
            return config_io
        except KeyError:
            raise ValueError(f"unknown config file extension: '{ext}'") from None

    def update(self, ext: str, config_io: ConfigIO) -> None:
        """
        Add or update the IO for an extension.

        Parameters
        ----------
        ext : str
            The file extension to add IO for.
            Extensions should include the starting period (``.``).
        config_io : ConfigIO
            The IO to use for files with extension `ext`.

        Raises
        ------
        ValueError
            If `ext` does not start with a period (``.``).
        """
        if len(ext) > 0 and not ext.startswith("."):
            raise ValueError(f"'{ext}' does not start with a period")

        self._ext_io_map[ext.lower()] = config_io

    def read(self, path):
        return self._retrieve_io(path).read(path)

    def write(self, config, path):
        return self._retrieve_io(path).write(config, path)
