import keyword
import re
import warnings
from abc import abstractmethod
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
    Optional,
    ItemsView,
    KeysView,
    ValuesView,
    Collection,
    Hashable,
)

__all__ = [
    "ConfigurationBase",
    "PlainConfiguration",
    "FrozenConfiguration",
    "Configuration",
    "InvalidKeyError",
]

V = TypeVar("V")
Self = TypeVar("Self", bound="ConfigurationBase")
_MappingLike = Union[Mapping[str, Any], Iterable[Tuple[str, Any]]]


class InvalidKeyError(ValueError):
    """Raised when a key can not be used in a configuration object."""

    pass


class ConfigurationBase(Mapping[str, V]):
    """
    Interface for configuration that maps variable names to their values.

    A `ConfigurationBase` object can be used to represent values for various values.
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

    # TODO: drop py3.6 support for proper generics?
    class FlatConfigView(Collection):
        """Flat view of configuration object."""

        __slots__ = "_config"

        def __init__(self, config: "ConfigurationBase"):
            self._config = config

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self._config!r})"

        def __len__(self) -> int:
            return sum(1 for _ in self.__iter__())

        @abstractmethod
        def __contains__(self, item: Any) -> bool:
            raise NotImplementedError("subclass must implement this method")

        @abstractmethod
        def __iter__(self):
            raise NotImplementedError("subclass must implement this method")

        def _flat_iter(self) -> Iterator[Tuple[str, V]]:
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
            for key, value in self._config.__dict__.items():
                if isinstance(value, self._config.__class__):
                    yield from (
                        (".".join([key, sub_key]), v)
                        for sub_key, v in ConfigurationBase.FlatItemsView(value)
                    )
                else:
                    yield key, value

    class FlatItemsView(FlatConfigView):
        """Flat view of key-value pairs in configuration."""

        def __contains__(self, item):
            k, v = item
            try:
                value = self._config[k]
            except KeyError:
                return False
            else:
                return not isinstance(v, self._config.__class__) and (
                    v is value or v == value
                )

        def __iter__(self):
            yield from self._flat_iter()

    class FlatKeysView(FlatConfigView):
        """Flat view of keys in configuration."""

        def __contains__(self, key):
            try:
                val = self._config[key]
            except KeyError:
                return False
            else:
                return not isinstance(val, self._config.__class__)

        def __iter__(self):
            yield from (k for k, _ in self._flat_iter())

    class FlatValuesView(FlatConfigView):
        """Flat view of values in configuration."""

        def __contains__(self, value):
            return any(v is value or v == value for k, v in self._flat_iter())

        def __iter__(self):
            yield from (v for _, v in self._flat_iter())

    def __init__(self, **kwargs: V):
        pass

    def __repr__(self) -> str:
        kwargs = ["=".join([k, f"{v!r}"]) for k, v in self.__dict__.items()]
        return f"{self.__class__.__name__}({', '.join(kwargs)})"

    def __str__(self) -> str:
        kwargs = [": ".join([k, f"{v!s}"]) for k, v in self.__dict__.items()]
        return f"{{{', '.join(kwargs)}}}"

    # # # Attribute Access # # #

    def __getattr__(self, name: str) -> V:
        msg = f"'{self.__class__.__name__}' object has no attribute '{name}'"
        if "." in name:
            msg = f"dot-strings only work for indexing, try `config[{name}]` instead"

        raise AttributeError(msg)

    # # # Mapping Interface # # #

    def __getitem__(self, key: Union[str, Tuple[str, ...]]) -> V:
        conf, key = self._resolve_key(key)
        return conf.__dict__[key]

    def __len__(self) -> int:
        return self.__dict__.__len__()

    def __iter__(self) -> Iterator[str]:
        return iter(self.__dict__)

    # # # Merging # # #

    def __or__(self: Self, other: Mapping[str, Any]) -> Self:
        return self.__class__(**(PlainConfiguration(**self) | other))

    def __ror__(self: Self, other: Mapping[str, Any]) -> Self:
        return self.__class__(**(other | PlainConfiguration(**self)))

    # # # Flat Iterators # # #

    @overload
    def keys(self) -> KeysView:
        ...

    @overload
    def keys(self, flat: bool = ...) -> Union[KeysView, FlatKeysView]:
        ...

    def keys(self, flat=False):
        """
        Get a view of this configuration's keys.

        Parameters
        ----------
        flat : bool, optional
            If ``True``, the view will ignore the hierarchy of this config.
            This means that instead of returning subconfigs,
            the subconfigs are recursively included in the view.
            Keys of subconfigs are combined with the keys in the subconfig
            with a ``.`` so that they are valid indices for this configuration.
            If ``False`` (Default), a regular ``dict``-like view will be returned.

        Returns
        -------
        keys_view : KeysView or FlatKeysView
            The new view on the keys in this config.

        Examples
        --------
        >>> conf = PlainConfiguration(a=123, sub=PlainConfiguration(b="foo", c=None))
        >>> list(conf.keys())
        ['a', 'sub']
        >>> list(conf.keys(flat=True))
        ['a', 'sub.b', 'sub.c']
        """
        if not flat:
            return self.__dict__.keys()

        return self.__class__.FlatKeysView(self)

    @overload
    def items(self) -> ItemsView:
        ...

    @overload
    def items(self, flat: bool = ...) -> Union[ItemsView, FlatItemsView]:
        ...

    def items(self, flat=False):
        """
        Get a view of this configuration's `(key, value)` pairs.

        Parameters
        ----------
        flat : bool, optional
            If ``True``, the view will ignore the hierarchy of this config.
            This means that instead of returning subconfigs,
            the subconfigs are recursively included in the view.
            Keys of subconfigs are combined with the keys in the subconfig
            with a ``.`` so that they are valid indices for this configuration.
            If ``False`` (Default), a regular ``dict``-like view will be returned.

        Returns
        -------
        keys_view : ItemsView or FlatItemsView
            The new view on the `(key, value)` pairs in this config.

        Examples
        --------
        >>> conf = PlainConfiguration(a=123, sub=PlainConfiguration(b="foo", c=None))
        >>> list(conf.items())
        [('a', 123), ('sub', PlainConfiguration(b='foo', c=None))]
        >>> list(conf.items(flat=True))
        [('a', 123), ('sub.b', 'foo'), ('sub.c', None)]
        """
        if not flat:
            return self.__dict__.items()

        return self.__class__.FlatItemsView(self)

    @overload
    def values(self) -> ValuesView:
        ...

    @overload
    def values(self, flat: bool = ...) -> Union[ValuesView, FlatValuesView]:
        ...

    def values(self, flat=False):
        """
        Get a view of this configuration's values.

        Parameters
        ----------
        flat : bool, optional
            If ``True``, the view will ignore the hierarchy of this config.
            This means that instead of returning subconfigs,
            the subconfigs are recursively included in the view.
            Keys of subconfigs are combined with the keys in the subconfig
            with a ``.`` so that they are valid indices for this configuration.
            If ``False`` (Default), a regular ``dict``-like view will be returned.

        Returns
        -------
        keys_view : ValuesView or FlatValuesView
            The new view on the values in this config.

        Examples
        --------
        >>> conf = PlainConfiguration(a=123, sub=PlainConfiguration(b="foo", c=None))
        >>> list(conf.values())
        [123, PlainConfiguration(b='foo', c=None)]
        >>> list(conf.values(flat=True))
        [123, 'foo', None]
        """
        if not flat:
            return self.__dict__.values()

        return self.__class__.FlatValuesView(self)

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
            keys = tuple(keys.split("."))
        elif not isinstance(keys, tuple):
            msg = f"index must be string or a tuple of strings, but got '{type(keys)}'"
            raise TypeError(msg)
        elif len(keys) == 0:
            raise InvalidKeyError("empty tuple")

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

    @classmethod
    @overload
    def _fix_value(
        cls: Type[Self], value: Mapping[str, Any], old_val: Any = None
    ) -> Self:
        ...

    @classmethod
    @overload
    def _fix_value(cls, value: V, old_val: Any = None) -> V:
        ...

    @classmethod
    def _fix_value(cls, value, old_val=None):
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
            value = cls(**value)
            old_val |= value
            return old_val
        except TypeError:
            return value

    # # # Dict Conversion # # #

    @classmethod
    def from_dict(
        cls: Type[Self],
        mapping: Mapping[str, V],
        key_mods: Optional[Mapping[str, str]] = None,
    ) -> Self:
        if key_mods is None:
            key_mods = {}

        return cls(**_modify_keys(mapping.items(), key_mods))

    def to_dict(
        self, key_mods: Optional[Mapping[str, str]] = None, flat: bool = False
    ) -> Dict[str, V]:
        if key_mods is None:
            key_mods = {}

        return _modify_keys(self.items(flat=flat), key_mods)


class PlainConfiguration(ConfigurationBase[Any], MutableMapping[str, Any]):
    """
    Freely mutable configuration.

    A `PlainConfiguration` object is a mutable implementation of a `ConfigurationBase`.
    This means that you can add, change and/or delete values in this object.
    Moreover, there are no limitations to the changes you can make.
    Concretely, you are able to:
        - overwrite values without warnings or errors,
        - use variable names that are not valid attribute names,
        - use attribute or method names as keys.

    See Also
    --------
    `FrozenConfiguration`: an immutable configuration.

    Notes
    -----
    In the current implementation, using method names as keys is possible,

    >>> conf = PlainConfiguration()
    >>> print(conf.items)
    <bound method ConfigurationBase.items of PlainConfiguration()>
    >>> conf["items"] = 123
    >>> print(conf.items)
    123

    but it can lead to some unexpected behaviour.

    >>> print(conf)
    {items: 123}
    >>> conf == {"items": 123}
    Traceback (most recent call last):
        ...
    TypeError: 'int' object is not callable

    Examples
    --------
    Starting with a simple configuration.

    >>> conf = PlainConfiguration(foo=0, bar="bar", baz={'a': 1, 'b': 2})
    >>> print(conf)
    {foo: 0, bar: bar, baz: {a: 1, b: 2}}

    Variables can be added, changed or removed as desired.

    >>> conf.surprise = None
    >>> print(conf)
    {foo: 0, bar: bar, baz: {a: 1, b: 2}, surprise: None}
    >>> conf["surprise"] = []
    >>> print(conf)
    {foo: 0, bar: bar, baz: {a: 1, b: 2}, surprise: []}
    >>> del conf.baz.a
    >>> print(conf)
    {foo: 0, bar: bar, baz: {b: 2}, surprise: []}

    Creating a single value in a subconfig is only possible using indexing syntax.

    >>> conf.sub.val = 0
    Traceback (most recent call last):
        ...
    AttributeError: 'PlainConfiguration' object has no attribute 'sub'
    >>> conf["sub", "val"] = -1
    >>> print(conf)
    {foo: 0, bar: bar, baz: {b: 2}, surprise: [], sub: {val: -1}}
    >>> conf['surprise'] = {"val": "tada"}
    >>> print(conf)
    {foo: 0, bar: bar, baz: {b: 2}, surprise: {val: tada}, sub: {val: -1}}
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        self.update(**kwargs)

    # # # Attribute Access # # #

    def __setattr__(self, name: str, value: Any) -> None:
        if "." in name:
            msg = f"dot-strings only work for indexing, try `config[{name}]` instead"
            raise AttributeError(msg)

        super().__setattr__(name, self._fix_value(value))

    def __delattr__(self, name: str) -> Any:
        if "." in name:
            msg = f"dot-strings only work for indexing, try `config[{name}]` instead"
            raise AttributeError(msg)

        return super().__delattr__(name)

    # # # Mapping Interface # # #

    def __setitem__(self, key: Union[str, Tuple[str, ...]], value: Any) -> None:
        conf, key = self._resolve_key(key, create=True)
        conf.__dict__[key] = self._fix_value(value)

    def __delitem__(self, key: Union[str, Tuple[str, ...]]) -> None:
        conf, key = self._resolve_key(key)
        del conf.__dict__[key]

    # # # Merging # # #

    def __or__(self, other):
        result = self.__class__(**self)
        result |= other
        return result

    def __ror__(self, other):
        result = self.__class__(**other)
        result |= self
        return result

    def __ior__(self, other):
        for k, v in other.items():
            self[k] = self._fix_value(v, self.get(k, None))
        return self


class FrozenConfiguration(ConfigurationBase[Hashable], Hashable):
    """
    Immutable configuration.

    A `FrozenConfiguration` object is an immutable implementation of a `ConfigurationBase`.
    This means that you can **not** add, change and/or delete anything in this object.
    Because of this immutability, `FrozenConfiguration` is a `Hashable` type,
    which means that they can be used in ``set``s and serve as keys in a ``dict``.

    See Also
    --------
    `PlainConfiguration`: a mutable configuration.

    Notes
    -----
    In the current implementation, using method names as keys is possible,

    >>> conf = FrozenConfiguration()
    >>> print(conf.items)
    <bound method ConfigurationBase.items of FrozenConfiguration()>
    >>> conf = FrozenConfiguration(items=123)
    >>> print(conf.items)
    123

    but it can lead to some unexpected behaviour.

    >>> print(conf)
    {items: 123}
    >>> conf == {"items": 123}
    Traceback (most recent call last):
        ...
    TypeError: 'int' object is not callable

    Examples
    --------
    Starting with a simple configuration.

    >>> conf = FrozenConfiguration(foo=0, bar="bar", baz={'a': 1, 'b': 2})
    >>> print(conf)
    {foo: 0, bar: bar, baz: {a: 1, b: 2}}

    Attempts to change the configuration will result in errors.

    >>> conf.surprise = None
    Traceback (most recent call last):
        ...
    AttributeError: 'FrozenConfiguration' object has no attribute 'surprise'
    >>> conf["surprise"] = []
    Traceback (most recent call last):
        ...
    TypeError: 'FrozenConfiguration' object does not support item assignment
    >>> del conf.baz.a
    Traceback (most recent call last):
        ...
    AttributeError: 'FrozenConfiguration' object attribute 'a' is read-only

    Values are converted to hashable types if possible.

    >>> print(FrozenConfiguration(value=[1, 2, 3]))
    {value: (1, 2, 3)}
    >>> print(FrozenConfiguration(value=slice(None)))
    Traceback (most recent call last):
        ...
    TypeError: unhashable type: 'slice'

    The main feature is that frozen configurations can be used as ``dict`` keys.

    >>> results = {
    ...     FrozenConfiguration(option=1): 0.1,
    ...     FrozenConfiguration(option=2): 0.9,
    ... }
    >>> print(max(results.items(), key=lambda kv: kv[1]))
    (FrozenConfiguration(option=2), 0.9)
    """

    def __init__(self, **kwargs: Union[Hashable, Collection, Mapping]):
        super().__init__()
        for k, v in kwargs.items():
            v = self._fix_value(v)
            conf, k = self._resolve_key(k, create=True)
            conf.__dict__[k] = v

    def __hash__(self) -> int:
        # inspired by https://stackoverflow.com/questions/20832279
        h = len(self)
        for k, v in self.items():
            hx = hash((k, v))
            h ^= (hx ^ 0x156B45B3 ^ (hx << 16)) * 4_155_791_671  # randomise
            h &= 0xFFFF_FFFF_FFFF_FFFF  # limit to 8 bytes

        return h

    # # # Attribute Access # # #

    def __setattr__(self, name: str, value: Any = None) -> None:
        _ = getattr(self, name)  # recycle errors from getattr
        raise AttributeError(
            f"'{self.__class__.__name__}' object attribute '{name}' is read-only"
        )

    __delattr__ = __setattr__

    @classmethod
    def _fix_value(cls, value, old_val=None):
        def _make_hashable(o):
            if isinstance(o, Hashable):
                return o
            elif isinstance(o, Mapping):
                return cls(**o)
            elif isinstance(o, Collection):
                return tuple(_make_hashable(v) for v in o)

            raise TypeError(f"unhashable type: '{type(o).__name__}'")

        return super()._fix_value(_make_hashable(value), old_val)


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
