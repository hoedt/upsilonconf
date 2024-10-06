import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Mapping,
    Any,
    Union,
    TextIO,
    Sequence,
    Dict,
    Optional,
    MutableMapping,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from ..config import ConfigurationBase

CONFIG_VAL_TYPE = Union[bool, int, float, str, Sequence, Mapping[str, Any]]


class ConfigIO(ABC):
    """
    Interface for reading/writing configurations to/from files.

    .. versionadded:: 0.5.0
    """

    # TODO: shouldn't encoding be part of the specific IO?
    #       e.g. JSON proposes utf-8 as standard (https://www.rfc-editor.org/rfc/rfc8259#section-8)
    #       e.g. YAML accepts utf-8, utf-16 and utf-32 (https://yaml.org/spec/1.2.2/#chapter-5-character-productions)
    #       e.g. TOML explicitly requires utf-8 (https://toml.io/en/v1.0.0)

    @property
    @abstractmethod
    def extensions(self) -> Sequence[str]:
        """Collection of extensions that are supported by this IO."""
        ...

    @property
    def default_ext(self) -> str:
        """Default extension for this IO."""
        return self.extensions[0]

    @abstractmethod
    def read_from(self, stream: TextIO) -> Mapping[str, Any]:
        """
        Read configuration from a file-like object.

        Parameters
        ----------
        stream : TextIO
            Readable character stream (file-like object).

        Returns
        -------
        config : dict
            A dictionary representing the configuration in the stream.

        Raises
        ------
        TypeError
            If the implementation does not support reading from a stream.
        """
        ...

    def parse_value(self, val: str) -> CONFIG_VAL_TYPE:
        """
        Parse string representing a value for a configuration without key.

        .. versionadded:: 0.8.0

        Parameters
        ----------
        val : str
            The string representing the value.

        Returns
        -------
        obj : any basic type
            The value object represented by `val`.
        """
        from io import StringIO

        return self.read_from(StringIO(val))

    def read(
        self, path: Union[Path, str], encoding: str = "utf-8"
    ) -> Mapping[str, Any]:
        """
        Read configuration from a file.

        Parameters
        ----------
        path : Path
            Path to a readable text file.
        encoding : str, optional
            The character encoding to use for the given file.

        Returns
        -------
        config : dict
            A dictionary representing the configuration in the file.
        """
        # add cwd for correct behaviour on Windows
        path = Path.resolve(Path.cwd() / Path(path).expanduser())
        with open(path, "r", encoding=encoding) as fp:
            return self.read_from(fp)

    def load_config(
        self,
        path: Union[Path, str],
        key_mods: Optional[Mapping[str, str]] = None,
        frozen: bool = False,
    ) -> "ConfigurationBase":
        """
        Load configuration from a file.

        .. deprecated:: 0.8.0
            ConfigIO.load_config will be replaced by ConfigurationBase.load

        Parameters
        ----------
        path : Path or str
            Path to a readable text file on disk.
        key_mods : dict, optional
            A mapping from key patterns to their respective replacement.
            With multiple patterns, longer patterns are replaced first.
        frozen : bool, optional
            If ``True``, an immutable configuration object will be created.
            If ``False`` (the default), a mutable configuration object is returned.

        Returns
        -------
        config : ConfigurationBase
            A configuration object with the values as provided in the file.

        See Also
        --------
        ConfigurationBase.from_dict : method used for key modifications
        PlainConfiguration : mutable configuration type
        FrozenConfiguration : immutable configuration type
        """
        from ..config import FrozenConfiguration, PlainConfiguration

        warnings.warn(
            "ConfigIO.load_config will be replaced by ConfigurationBase.load",
            DeprecationWarning,
            stacklevel=2,
        )

        Config = FrozenConfiguration if frozen else PlainConfiguration
        return Config.load(path, key_mods=key_mods, io=self)

    @abstractmethod
    def write_to(self, stream: TextIO, conf: Mapping[str, Any]) -> None:
        """
        Write configuration to a file-like object.

        Parameters
        ----------
        stream : TextIO
            Writeable character stream (file-like object).
        conf : Mapping
            A dictionary representing the configuration to be written.

        Raises
        ------
        TypeError
            If the implementation does not support writing to a stream.
        """
        ...

    def write(
        self, conf: Mapping[str, Any], path: Union[Path, str], encoding: str = "utf-8"
    ) -> None:
        """
        Write configuration to a file.

        Parameters
        ----------
        conf : Mapping
            A dictionary representing the configuration to be written.
        path : Path or str
            Path to a writeable text file.
        encoding : str, optional
            The character encoding to use for the given file.
        """
        # add cwd for correct behaviour on Windows
        path = Path.resolve(Path.cwd() / Path(path).expanduser())
        with open(path, "w", encoding=encoding) as fp:
            self.write_to(fp, conf)

    def save_config(
        self,
        config: "ConfigurationBase",
        path: Union[Path, str],
        key_mods: Optional[Mapping[str, str]] = None,
    ) -> None:
        """
        Save configuration to a file.

        .. deprecated:: 0.8.0
            ConfigIO.save_config will be replaced by ConfigurationBase.save

        Parameters
        ----------
        config : ConfigurationBase
            The configuration object to save.
        path : Path or str
            Path to a writeable location on disk.
        key_mods : dict, optional
            A mapping from key patterns to their respective replacement.
            With multiple patterns, longer patterns are replaced first.

        See Also
        --------
        ConfigurationBase.to_dict : method used for key modifications
        """
        warnings.warn(
            "ConfigIO.save_config will be replaced by ConfigurationBase.save",
            DeprecationWarning,
            stacklevel=2,
        )

        return config.save(path, key_mods=key_mods, io=self)


class ExtensionIO(ConfigIO, MutableMapping[str, ConfigIO]):
    """
    IO for selecting IOs based on file extensions.

    This IO is a mapping from file extensions to other IO objects.
    Whenever a file is to be read/written,
    the correct IO is chosen based on the file extension.

    .. versionadded:: 0.7.0

    Parameters
    ----------
    io : ConfigIO
        One of the IO objects to be included.
        Extensions of this IO will be extracted automatically.
    *more_ios : ConfigIO
        Other IO objects to be included.
        Extensions of these IOs will be extracted automatically.
    default_ext : str, optional
        The extension to use when the file-extension is unknown.
        E.g. when reading from a file-like object.
        If not specified, the default extension of `io` is used.
    """

    @staticmethod
    def _canonical_extension(ext: str) -> str:
        """
        Transform a string to a canonical form for extensions.

        Parameters
        ----------
        ext : str
            Sequence of characters that should represent an extension.

        Returns
        -------
        canonical_ext : str
            The canonical extension (with leading period).
        """
        if len(ext) > 0 and not ext.startswith("."):
            ext = f".{ext}"

        return ext.lower().strip()

    def __init__(
        self, io: ConfigIO, *more_ios: ConfigIO, default_ext: Optional[str] = None
    ):
        self._default_ext = None
        self._ext2io = {ext: io for io in (io,) + more_ios for ext in io.extensions}
        self.default_ext = io.default_ext if default_ext is None else default_ext

    def __getitem__(self, ext: str):
        return self._ext2io[self._canonical_extension(ext)]

    def __setitem__(self, ext: str, io: ConfigIO):
        self._ext2io[self._canonical_extension(ext)] = io

    def __delitem__(self, ext: str):
        ext = self._canonical_extension(ext)
        if ext == self.default_ext:
            raise ValueError("default extension can not be deleted")

        del self._ext2io[ext]

    def __len__(self):
        return len(self._ext2io)

    def __iter__(self):
        yield self.default_ext
        yield from filter(lambda ext: ext != self.default_ext, self._ext2io)

    @property
    def extensions(self):
        return tuple(iter(self))

    @property
    def default_ext(self):
        return self._default_ext

    @default_ext.setter
    def default_ext(self, ext: str):
        ext = self._canonical_extension(ext)
        if ext not in self._ext2io:
            msg = f"default extension '{ext}' not supported by provided IOs"
            raise ValueError(msg)

        self._default_ext = ext

    def read_from(self, stream):
        cls_name = self.__class__.__name__
        raise TypeError(f"{cls_name} does not support reading from stream")

    def parse_value(self, val):
        tried_ios = set()
        for ext, io in self.items():
            if io not in tried_ios:
                try:
                    return io.parse_value(val)
                except ValueError:
                    warnings.warn(
                        f"failed to parse value with '{ext}' IO, trying next IO",
                        RuntimeWarning,
                        stacklevel=2,
                    )
                finally:
                    tried_ios.add(io)

        info = f"with extensions {self.extensions}"
        raise ValueError(f"none of the IOs {info} could parse the value")

    def read(self, path, encoding="utf-8"):
        path = Path(path)
        try:
            return self[path.suffix].read(path, encoding)
        except KeyError:
            msg = f"unsupported config file extension: '{path.suffix}'"
            raise ValueError(msg) from None

    def write_to(self, stream, config):
        cls_name = self.__class__.__name__
        raise TypeError(f"{cls_name} does not support writing to stream")

    def write(self, config, path, encoding="utf-8"):
        path = Path(path)
        try:
            return self[path.suffix].write(config, path, encoding)
        except KeyError:
            msg = f"unsupported config file extension: '{path.suffix}'"
            raise ValueError(msg) from None


class FlexibleIO(ConfigIO):
    """
    IO for selecting IOs based on file extensions.

    This IO keeps a mapping from file extensions to their corresponding IOs.
    Whenever a file needs to be read/written, the file extension is used
    to retrieve the correct IO and forward the read/write operation.

    .. versionadded:: 0.5.0
    .. deprecated:: 0.7.0
        `FlexibleIO` will be removed in a future version in favour of `ExtensionIO`.

    Parameters
    ----------
    ext_io_map : Mapping[str, ConfigIO]
        A ``dict``-like object mapping extensions to the corresponding IO.
        The file extension should include the starting period (``.``).
    default_ext : str, optional
        The extension (and corresponding IO) to use
        when no information on the file-extension is available.
        If not specified, the first key in `ext_io_map` is used.
    """

    def __init__(
        self, ext_io_map: Mapping[str, ConfigIO], default_ext: Optional[str] = None
    ):
        warnings.warn(
            "FlexibleIO has been deprecated, use ExtensionIO instead",
            DeprecationWarning,
        )
        if len(ext_io_map) == 0:
            raise ValueError("at least one extension-IO pair is required")

        self._ext_io_map: Dict[str, ConfigIO] = {}
        ext_io_map = dict(ext_io_map)

        try:
            if default_ext is not None:
                self.update(default_ext, ext_io_map.pop(default_ext))
        except KeyError:
            raise ValueError(
                f"no IO registered for extension '{default_ext}'"
            ) from None

        for ext, io in ext_io_map.items():
            self.update(ext, io)

    def _retrieve_io(self, path: Optional[Path] = None) -> ConfigIO:
        """
        Retrieve IO to read/write config files given a path.

        Parameters
        ----------
        path: Path, optional
            Path to infer the file format from.
            If not specified, the IO corresponding to
            the default extension is returned.

        Returns
        -------
        config_io : ConfigIO
            Object for reading/writing config files from/to `path`.
        """
        ext = self.default_ext if path is None else path.suffix.lower()
        try:
            config_io = self._ext_io_map[ext]
            return config_io
        except KeyError:
            raise ValueError(f"unknown config file extension: '{ext}'") from None

    @property
    def extensions(self):
        return tuple(self._ext_io_map.keys())

    @property
    def default_io(self) -> ConfigIO:
        """IO corresponding to the default extension."""
        return self._retrieve_io()

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
            raise ValueError(f"extension '{ext}' does not start with a period")

        self._ext_io_map[ext.lower()] = config_io

    def read_from(self, stream):
        return self.default_io.read_from(stream)

    def read(self, path, encoding="utf-8"):
        return self._retrieve_io(path).read(path, encoding)

    def write_to(self, stream, config):
        self.default_io.write_to(stream, config)

    def write(self, config, path, encoding="utf-8"):
        return self._retrieve_io(path).write(config, path, encoding)
