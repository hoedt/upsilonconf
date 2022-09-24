import copy
import re
from typing import (
    MutableMapping,
    Any,
    Iterator,
    Iterable,
    Union,
    Tuple,
    Mapping,
    Dict,
    Pattern,
)

__all__ = ["Configuration", "InvalidKeyError"]

_MappingLike = Union[Mapping[str, Any], Iterable[Tuple[str, Any]]]


class InvalidKeyError(ValueError):
    """Raised when a key can not be used in a configuration object."""

    pass


class Configuration(MutableMapping[str, Any]):
    """
    Configuration mapping (variable) names to their corresponding values.

    A `Configuration` should provide a convenient way to store
    (hyper-)parameters for your code and/or experiments.
    Any configuration value that represents a mapping is also automagically
    converted to a `Configuration` to build arbitrary config hierarchies.

    This class provides an interface that is similar to that of a dictionary.
    Additionally, it allows to access parameters as attributes.
    This means that you can simply use attribute syntax,
    instead of writing brackets and strings everywhere.
    To allow easy access to values in sub-configurations,
    sequences of indices can be used instead of chained indexing.
    Similarly, a string with parameter names separated by dots
    will be automagically split in a tuple index for easy access.

    Additional parameter values can be added to the mapping as needed.
    However, to avoid unwanted changes to configuration values,
    it is not possible to directly set the value for existing parameters.
    If you deliberately wish to set the value for existing parameters,
    you should use the `overwrite` method instead.

    Methods
    -------
    overwrite(key, value)
        Explicitly overwrite an existing parameter value in the configuration.
    overwrite_all(m, **kwargs)
        Explicitly overwrite multiple existing parameter values in the configuration.

    Examples
    --------
    >>> conf = Configuration(foo=0, bar="bar", baz={'a': 1, 'b': 2})
    >>> print(conf)
    {foo: 0, bar: bar, baz: {a: 1, b: 2}}
    >>> conf['bar']
    'bar'
    >>> conf['baz']['a']
    1

    Values can also be accessed as attributes, tuples or a string with dots

    >>> conf.bar
    'bar'
    >>> conf.baz.a
    1
    >>> conf['baz', 'a']
    1
    >>> conf['baz.a']
    1

    Values for new parameters can be added directly.
    To avoid inadvertadly overwriting values, the `overwrite` method must be used.

    >>> conf.new = "works"
    >>> conf['new'] = "won't work"
    Traceback (most recent call last):
        ...
    ValueError: key 'new' already defined, use 'overwrite' methods instead
    >>> conf.overwrite('new', "will work")
    'works'
    >>> conf.new
    'will work'
    """

    def __init__(self, **kwargs):
        self._content: MutableMapping[str, Any] = {}

        for k, v in kwargs.items():
            self.__setitem__(k, v)

    def __repr__(self) -> str:
        kwargs = ["=".join([k, "{!r}".format(v)]) for k, v in self.items()]
        return f"{self.__class__.__name__}({', '.join(kwargs)})"

    def __str__(self) -> str:
        kwargs = [": ".join([k, "{!s}".format(v)]) for k, v in self.items()]
        return f"{{{', '.join(kwargs)}}}"

    def __getstate__(self) -> Mapping[str, Any]:
        return {k: v for k, v in self.items()}

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        self.__init__(**state)

    def __copy__(self) -> "Configuration":
        return Configuration(**self)

    def __deepcopy__(self, memo: Dict = None) -> "Configuration":
        if memo is None:
            memo = {}

        result = Configuration()
        for k, v in self.items():
            result[k] = copy.deepcopy(v, memo=memo)

        return result

    # # # Mapping Interface # # #

    def __getitem__(self, key: Union[str, Iterable[str]]) -> Any:
        conf, key = self._resolve_key(key)
        return conf._content.__getitem__(key)

    def __setitem__(self, key: Union[str, Iterable[str]], value: Any) -> None:
        conf, key = self._resolve_key(key, create=True)
        conf._validate_key(key)
        if key in conf._content:
            msg = f"key '{key}' already defined, use 'overwrite' methods instead"
            raise ValueError(msg)

        try:
            value = Configuration(**value)
        except TypeError:
            pass

        return conf._content.__setitem__(key, value)

    def __delitem__(self, key: Union[str, Iterable[str]]) -> None:
        conf, key = self._resolve_key(key)
        return conf._content.__delitem__(key)

    def __len__(self) -> int:
        return self._content.__len__()

    def __iter__(self) -> Iterator[Any]:
        return self._content.__iter__()

    # # # Merging # # #

    def __or__(self, other: Mapping[str, Any]):
        result = Configuration(**self)
        result.update(other)
        return result

    def __ror__(self, other: Mapping[str, Any]):
        result = Configuration(**other)
        result.update(self)
        return result

    def __ior__(self, other: Mapping[str, Any]):
        self.update(**other)
        return self

    # # # Attribute Access # # #

    def __getattr__(self, name: str) -> Any:
        try:
            self._validate_key(name)
            return self.__getitem__(name)
        except InvalidKeyError:
            msg = f"'{self.__class__.__name__}' object has no attribute '{name}'"
            raise AttributeError(msg) from None
        except KeyError:
            raise AttributeError(f"no config entry with key '{name}'") from None

    def __setattr__(self, name: str, value: Any) -> None:
        try:
            self.__setitem__(name, value)
        except InvalidKeyError:
            super().__setattr__(name, value)
        except ValueError as e:
            raise AttributeError(f"config entry with key " + str(e)) from None

    def __delattr__(self, name: str) -> None:
        try:
            self._validate_key(name)
            self.__delitem__(name)
        except InvalidKeyError:
            msg = f"'{self.__class__.__name__}' object has no attribute '{name}'"
            raise AttributeError(msg) from None
        except KeyError:
            raise AttributeError(f"no config entry with key '{name}'") from None

    def __dir__(self) -> Iterable[str]:
        yield from super().__dir__()
        yield from self._content

    # # # Other Stuff # # #

    def _validate_key(self, key: str) -> True:
        """
        Check if a key respects a set of simple rules.

        Raises
        ------
        InvalidKeyError
            If the key does not respect the rules.
        """
        if len(key) == 0 or not key[0].isalpha():
            raise InvalidKeyError(f"'{key}' does not start with a letter")
        if not key.isidentifier():
            raise InvalidKeyError(f"'{key}' contains symbols that are not allowed")
        if key in super().__dir__():
            raise InvalidKeyError(f"'{key}' is not allowed as key, it is special")

        return True

    def _resolve_key(
        self, keys: Union[str, Iterable[str]], create: bool = False
    ) -> Tuple["Configuration", str]:
        """
        Resolve dot-string and iterable keys

        Parameters
        ----------
        keys : str or iterable of str
            The key(s) to be resolved.
        create : bool, optional
            If ``True``, non-existent sub-configurations will be created.

        Returns
        -------
        config: Configuration
            The sub-configuration that should host the final key (and value).
        key : str
            The final key that should correspond to the actual value.

        Raises
        ------
        KeyError
            If any of the sub-keys (apart from the final key)
            point to a value that is not a configuration.
        """
        try:
            *parents, final = keys.split(".")
        except AttributeError:
            *parents, final = keys

        root = self
        for k in parents:
            try:
                root = root[k]
            except KeyError:
                if not create:
                    raise

                root[k] = {}
                root = root[k]
            else:
                if not isinstance(root, Configuration):
                    raise KeyError(k)

        return root, final

    def overwrite(self, key: Union[str, Iterable[str]], value: Any) -> Any:
        """
        Overwrite a possibly existing parameter value in the configuration.

        Parameters
        ----------
        key : str or iterable of str
            The parameter name to overwrite the value for.
        value
            The new value for the parameter.

        Returns
        -------
        old_value
            The value that has been overwritten
            or ``None`` if no value was present.

        See Also
        --------
        overwrite_all : overwrite multiple values in one go.
        """
        old_value = self.pop(key, None)
        try:
            sub_conf = Configuration(**old_value)
            old_value = sub_conf.overwrite_all(value)
            value = sub_conf
        except TypeError:
            pass

        self.__setitem__(key, value)
        return old_value

    def overwrite_all(self, other: _MappingLike = (), **kwargs) -> Mapping[str, Any]:
        """
        Overwrite multiple possibly existing parameter value in this configuration.

        This method makes it possible to overwrite multiple values in one go.
        It should produce the same results as calling `update`
        when none of the keys are already contained in this configuration.
        Unlike `update`, however, this method will not raise an error
        if one or more of the keys already exist.

        Parameters
        ----------
        other : Mapping or iterable of tuples
            Dictionary-like object with values to overwrite.
        **kwargs
            Additional key-value pairs for overwrites.

        Returns
        -------
        old_values : Mapping
            Mapping from keys to the values that have been overwritten.
            If the key did not exist, the corresponding value is ``None``.

        See Also
        --------
        overwrite : overwrite single values.
        update : same functionality, but raises errors for duplicate keys.
        """
        old_values = {}

        try:
            for k in other.keys():
                old_values[k] = self.overwrite(k, other[k])
        except AttributeError:
            for k, v in other:
                old_values[k] = self.overwrite(k, v)

        for k, v in kwargs.items():
            old_values[k] = self.overwrite(k, v)

        return old_values

    # # # Dict Conversion # # #

    @staticmethod
    def from_dict(
        mapping: Mapping[str, Any],
        key_mods: Mapping[str, str] = None,
    ) -> "Configuration":
        """
        Create a configuration object from a given mapping.

        This method is especially useful to create a config from
        a mapping that contains keys with invalid characters.
        By means of `key_mods`, invalid characters can be
        replaced to create keys that would be accepted by `__init__`.

        Parameters
        ----------
        mapping : Mapping[str, Any]
            The mapping to be converted into a configuration.
        key_mods : Mapping[str, str], optional
            A mapping from key patterns to their replacements.

        Returns
        -------
        config : Configuration
            A configuration object representing the original mapping.

        See Also
        --------
        __init__ : regular configuration construction
        to_dict : convert configuration to dictionary

        Examples
        --------
        Invalid characters in keys of a dictionary might lead to problems.

        >>> d = {"key 1": "with space", "key-2": "with hyphen"}
        >>> Configuration(**d)
        Traceback (most recent call last):
          ...
        upsilonconf.config.InvalidKeyError: 'key 1' contains symbols that are not allowed

        By using `from_dict` with `key_mods`, invalid characters can be replaced.

        >>> Configuration.from_dict(d, key_mods={" ": "_", "-": "0"})
        Configuration(key_1='with space', key02='with hyphen')

        Construction will still fail if not all characters are addressed!

        >>> Configuration.from_dict(d, key_mods={" ": "_"})
        Traceback (most recent call last):
          ...
        upsilonconf.config.InvalidKeyError: 'key-2' contains symbols that are not allowed
        """
        if key_mods is None:
            key_mods = {}

        return Configuration(**_modify_keys(mapping, key_mods))

    def to_dict(self, key_mods: Mapping[str, str] = None) -> Dict[str, Any]:
        """
        Convert this configuration to a dictionary.

        This method implements the inverse of `from_dict`.
        It is especially useful to create a mapping
        without constraints on the format for keys.
        Also, it ensures that sub-configs are transformed recursively.

        Parameters
        ----------
        key_mods : Mapping[str, str], optional
            A mapping from key patterns to their replacements.

        Returns
        -------
        mapping : dict[str, Any]
            A dictionary with the same
            key-value pairs as this configuration.

        See Also
        --------
        from_dict : convert dictionary to configuration

        Examples
        --------
        In order to convert a nested configuration to a dictionary,
        it does not suffice to call ``dict``.

        >>> conf = Configuration(sub=Configuration(a=1))
        >>> dict(conf)
        {'sub': Configuration(a=1)}

        Using `to_dict` does work recursively.

        >>> conf.to_dict()
        {'sub': {'a': 1}}

        Similar to `from_dict`, key-modifiers can be used to transform keys.

        >>> conf = Configuration(key_1='with space', key02='with hyphen')
        >>> conf.to_dict(key_mods={"_": " ", "0": "-"})
        {'key 1': 'with space', 'key-2': 'with hyphen'}
        """
        if key_mods is None:
            key_mods = {}

        return _modify_keys(self, key_mods)


# utilities


def _modify_keys(
    mapping: Mapping[str, Any], key_mods: Mapping[str, str]
) -> Dict[str, Any]:
    """
    Replace strings in the keys of a mapping object recursively.

    Parameters
    ----------
    mapping : Mapping
        The mapping object whose keys are to be modified.
    key_mods : Mapping
        The dictionary with the replacements: All key strings are replaced
        with the corresponding values from this dictionary.

    Returns
    -------
    dict
        A dictionary with the modified keys.

    """
    # See https://github.com/hoedt/upsilonconf/pull/6 for alternative
    # implementations (and a discussion about them) which do not use regular
    # expressions.

    # Build and compile replacement pattern
    sorted_mod_keys = sorted(key_mods, key=lambda k: len(k), reverse=True)
    pattern = re.compile("|".join([re.escape(k) for k in sorted_mod_keys]))

    return __modify_keys(mapping, key_mods, pattern)


def __modify_keys(
    mapping: Mapping[str, Any], key_mods: Mapping[str, str], pattern: Pattern
) -> Dict[str, Any]:
    """
    Replace strings in the keys of a mapping object.

    This is the working horse for `_modify_keys` to do the replacement
    recursively.

    Parameters
    ----------
    mapping : Mapping
        The mapping object whose keys are to be modified.
    key_mods : Mapping
        The dictionary with the replacements: All key strings are replaced
        with the corresponding values from this dictionary.
    pattern : Pattern
        The compiled replacement pattern.

    Returns
    -------
    dict
        A dictionary with the modified keys.

    """
    dictionary = {}

    # `mapping.items()` fails with `AttributeError`, if `mapping` is not of a
    # mapping type, thus breaking the recursive calls
    for key, value in mapping.items():
        try:
            # Call this method recursively
            value = __modify_keys(value, key_mods, pattern)
        except AttributeError:
            # `value` is not of the mapping type
            pass

        # Replace only, if there are replacements requested, otherwise just
        # save the value
        if key_mods:
            dictionary[pattern.sub(lambda m: key_mods[m.group(0)], key)] = value
        else:
            dictionary[key] = value

    return dictionary
