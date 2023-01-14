import keyword
import re
import warnings
from typing import (
    TypeVar,
    MutableMapping,
    Any,
    Iterator,
    Iterable,
    Union,
    Tuple,
    Mapping,
    Dict,
    Pattern,
    overload,
    Type,
)

__all__ = ["PlainConfiguration", "Configuration", "InvalidKeyError"]

T = TypeVar("T")
Self = TypeVar("Self", bound="PlainConfiguration")
_MappingLike = Union[Mapping[str, Any], Iterable[Tuple[str, Any]]]


class InvalidKeyError(ValueError):
    """Raised when a key can not be used in a configuration object."""

    pass


class PlainConfiguration(MutableMapping[str, Any]):
    """
    Configuration that maps variable names to their corresponding values.

    A `PlainConfiguration` object can be used to collect values for various values.
    It can be interpreted in two ways:

    - a dictionary (or more generally, a mapping) with attribute syntax, or
    - a python object with indexing syntax.

    On top of the combined feature set of dictionaries and attributes,
    this class introduces advanced indexing, convenient merging and `dict` conversions.
    ``dict``-like values are automatically converted to `PlainConfiguration` objects,
    giving rise to hierarchical configuration objects.

    Examples
    --------
    Configurations are typically constructed from keyword arguments.

    >>> conf = PlainConfiguration(foo=0, bar="bar", baz={'a': 1, 'b': 2})
    >>> print(conf)
    {foo: 0, bar: bar, baz: {a: 1, b: 2}}

    A configuration is both ``object`` and ``Mapping`` at the same time.

    >>> conf['bar'] == conf.bar
    True
    >>> conf['baz']['a'] == conf.baz.a
    True

    Advanced indexing for convenient access to subconfigs.

    >>> conf['baz', 'a']  # tuple index
    1
    >>> conf['baz.a']  # dot-string index
    1

    Configurations can conveniently be merged with other ``Mapping`` objects.

    >>> print(conf | {"xtra": None})
    {foo: 0, bar: bar, baz: {a: 1, b: 2}, xtra: None}
    >>> print(conf | {"baz": {"c": 3}})
    {foo: 0, bar: bar, baz: {a: 1, b: 2, c: 3}}
    """

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def __repr__(self) -> str:
        kwargs = ["=".join([k, f"{v!r}"]) for k, v in self.items()]
        return f"{self.__class__.__name__}({', '.join(kwargs)})"

    def __str__(self) -> str:
        kwargs = [": ".join([k, f"{v!s}"]) for k, v in self.items()]
        return f"{{{', '.join(kwargs)}}}"

    # # # Mapping Interface # # #

    def __getitem__(self, key: Union[str, Tuple[str, ...]]) -> Any:
        conf, key = self._resolve_key(key)
        return conf.__dict__[key]

    def __setitem__(self, key: Union[str, Tuple[str, ...]], value: Any) -> None:
        conf, key = self._resolve_key(key, create=True)
        old_val = conf.__dict__.get(key, None)
        conf.__dict__[key] = self._fix_value(value, old_val)

    def __delitem__(self, key: Union[str, Tuple[str, ...]]) -> None:
        conf, key = self._resolve_key(key)
        del conf.__dict__[key]

    def __len__(self) -> int:
        return self.__dict__.__len__()

    def __iter__(self) -> Iterator[Any]:
        return iter(self.__dict__)

    # # # Merging # # #

    def __or__(self: Self, other: Mapping[str, Any]) -> Self:
        result = self.__class__(**self)
        result.update(other)
        return result

    def __ror__(self: Self, other: Mapping[str, Any]) -> Self:
        result = self.__class__(**other)
        result.update(self)
        return result

    def __ior__(self: Self, other: Mapping[str, Any]) -> Self:
        self.update(other)
        return self

    # # # Attribute Access # # #

    def __getattribute__(self, name: str) -> Any:
        if "." in name:
            msg = f"dot-strings only work for indexing, try `config[{name}]` instead"
            raise AttributeError(msg)

        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if "." in name:
            msg = f"dot-strings only work for indexing, try `config[{name}]` instead"
            raise AttributeError(msg)

        fixed_value = self._fix_value(value, old_val=self.get(name, None))
        super().__setattr__(name, fixed_value)

    def __delattr__(self, name: str) -> Any:
        if "." in name:
            msg = f"dot-strings only work for indexing, try `config[{name}]` instead"
            raise AttributeError(msg)

        return super().__delattr__(name)

    # # # Key Magic # # #

    def _resolve_key(
        self: Self, keys: Union[str, Tuple[str, ...]], create: bool = False
    ) -> Tuple[Self, str]:
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
        config: PlainConfiguration
            The sub-configuration that should host the final key (and value).
        key : str
            The final key that should correspond to the actual value.

        Raises
        ------
        KeyError
            If any of the sub-keys (apart from the final key)
            point to a value that is not a configuration.
        """
        if isinstance(keys, str):
            keys = keys.split(".")
        elif not isinstance(keys, tuple):
            msg = f"index must be string or a tuple of strings, but got '{type(keys)}'"
            raise TypeError(msg)

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
                if not isinstance(root, self.__class__):
                    raise KeyError(k)

        return root, final

    @overload
    def _fix_value(self: Self, value: Mapping[str, Any], old_val: Any) -> Self:
        ...

    @overload
    def _fix_value(self, value: T, old_val: Any) -> T:
        ...

    def _fix_value(self, value: Any, old_val: Any = None):
        """
        Prepare value for storage in this configuration.

        This method assures that the value satisfies the invariants
        and does not unnecessarily destroy the old value.

        Parameters
        ----------
        value
            The new value before storing.
        old_val (optional)
            The value that is going to be replaced by this value.

        Returns
        -------
        new_value
            The value that is ready to be stored.
        """
        try:
            value = self.__class__(**value)
            old_val |= value
            return old_val
        except TypeError:
            return value

    # # # Dict Conversion # # #

    @classmethod
    def from_dict(
        cls: Type[Self],
        mapping: Mapping[str, Any],
        key_mods: Mapping[str, str] = None,
    ) -> Self:
        if key_mods is None:
            key_mods = {}

        return cls(**_modify_keys(mapping.items(), key_mods))

    def to_dict(
        self, key_mods: Mapping[str, str] = None, flat: bool = False
    ) -> Dict[str, Any]:
        if key_mods is None:
            key_mods = {}

        items = self._flat_items() if flat else self.items()
        return _modify_keys(items, key_mods)


class Configuration(PlainConfiguration):
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

    def _resolve_key(
        self, keys: Union[str, Iterable[str]], create: bool = False
    ) -> Tuple["Configuration", str]:
        if not isinstance(keys, str):
            keys = tuple(keys)

        root, key = super()._resolve_key(keys, create)
        root._validate_key(key)
        if create and key in root.__dict__:
            msg = f"key '{key}' already defined, use 'overwrite' methods instead"
            raise ValueError(msg)

        return root, key

    # # # Attribute Access # # #

    def __setattr__(self, name: str, value: Any) -> None:
        try:
            self[name] = value
        except InvalidKeyError:
            raise AttributeError(f"can't set attribute '{name}'") from None
        except ValueError as e:
            raise AttributeError(str(e)) from None

    # # # Key Magic # # #

    def _flat_items(self) -> Iterable[Tuple[str, Any]]:
        """
        Iterate over key-value pairs of flat config.

        The flattened config uses dot-separated strings
        to represent values in sub-configs.

        Yields
        ------
        key : str
            A dot-separated key.
        value
            The value corresponding to that key.
        """
        # TODO: create proper ItemsView?
        # TODO: add other flat iterators?
        for k, v in self.items():
            if isinstance(v, self.__class__):
                yield from ((f"{k}.{_k}", _v) for _k, _v in v._flat_items())
            else:
                yield k, v

    def _validate_key(self, key: str) -> bool:
        """
        Check if a key respects a set of simple rules.

        Raises
        ------
        InvalidKeyError
            If the key does not respect the rules.
        """
        if not key.isidentifier() or keyword.iskeyword(key):
            warnings.warn(f"key {key!r} will not be accessible using attribute syntax")
        if len(key) > 0 and not key[0].isalpha():
            # TODO: should hidden attributes be allowed (as keys)?
            raise InvalidKeyError(f"{key!r} does not start with a letter")
        if key in dir(self.__class__):
            msg = f"using key {key!r} would break the interface of this object"
            raise InvalidKeyError(msg)

        return True

    # # # Overwriting # # #

    def overwrite(self, key: str, value: Any) -> Any:
        """
        Overwrite a possibly existing parameter value in the configuration.

        Parameters
        ----------
        key : str
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
        # TODO: this is practically a copy of __setitem__ now
        if not isinstance(key, str):
            key = tuple(key)
        conf, key = super()._resolve_key(key, create=True)
        old_value = conf.get(key, None)
        if old_value is None:
            conf._validate_key(key)

        try:
            sub_conf = self.__class__(**old_value)
            old_value = sub_conf.overwrite_all(value)
            value = sub_conf
        except TypeError:
            pass

        conf.__dict__.__setitem__(key, value)
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

        if isinstance(other, Mapping):
            other = other.items()

        for k, v in other:
            old_values[k] = self.overwrite(k, v)

        for k, v in kwargs.items():
            old_values[k] = self.overwrite(k, v)

        return old_values


# utilities


def _modify_keys(
    key_value_pairs: Iterable[Tuple[str, Any]], key_mods: Mapping[str, str]
) -> Dict[str, Any]:
    """
    Replace strings in the keys of a mapping object recursively.

    Parameters
    ----------
    key_value_pairs : Mapping
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

    return __modify_keys(key_value_pairs, key_mods, pattern)


def __modify_keys(
    key_value_pairs: Iterable[Tuple[str, Any]],
    key_mods: Mapping[str, str],
    pattern: Pattern,
) -> Dict[str, Any]:
    """
    Replace strings in the keys of a mapping object.

    This is the working horse for `_modify_keys` to do the replacement
    recursively.

    Parameters
    ----------
    key_value_pairs : Mapping
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
    for key, value in key_value_pairs:
        try:
            # Call this method recursively
            value = __modify_keys(value.items(), key_mods, pattern)
        except AttributeError:
            # `value` is not of the mapping type
            pass

        # Replace only, if there are replacements requested, otherwise just
        # save the value
        if key_mods:
            key = pattern.sub(lambda m: key_mods[m.group(0)], key)

        dictionary[key] = value

    return dictionary
