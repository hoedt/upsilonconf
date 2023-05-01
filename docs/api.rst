
API Reference
=============

.. currentmodule:: upsilonconf

The API of upsilonconf consists of mainly two parts.
The first part make up the main functionality:
configuration objects with a convenient interface.
The second part can be seen as the *included batteries*:
functions for conveniently storing and retrieving configuration objects.

.. contents::
    :local:

Configuration Objects
---------------------

Upsilonconf offers a few different configuration classes.
Mutable and immutable configuration types are provided by
:class:`PlainConfiguration` and :class:`FrozenConfiguration`, respectively.
The :class:`CarefulConfiguration` is a less pythonic configuration
that does not allow overwriting values by default.

All of these configuration types share a common interface.
This interface is provided by :class:`ConfigurationBase`.
Any class that inherits from this base class enables the features below.
For the examples, we will use :class:`PlainConfiguration`,
but these features are available in any of the provided implementations.

>>> from upsilonconf import PlainConfiguration as Config

Constructing Configurations
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Configurations objects can be created by the constructor.
The configuration entries can be specified by means of keyword arguments.

>>> conf = Config(key="value")
>>> print(conf)
{key: value}

Also a ``dict`` (or another mapping) can be directly passed to the constructor.
This is possible by the unpacking syntax in Python.

>>> conf = Config(**{"key": "value"})
>>> print(conf)
{key: value}

Alternatively, the :func:`~ConfigurationBase.from_dict` method can be used.
This method allows you to replace patterns in keys,
which can be useful to make keys valid attribute names.

>>> conf = Config.from_dict({"a key": "value"}, key_mods={" ": "_"})
>>> print(conf)
{a_key: value}

Any ``dict`` (or other mapping type) values will be converted to configuration objects.
This makes it easier to create hierarchical configuration object.

>>> conf = Config(sub={"key": "value"})
>>> print(conf)
{sub: {key: value}}

Configuration Attributes
^^^^^^^^^^^^^^^^^^^^^^^^

Each value in the configuration is also an attribute in the object.
The corresponding key in the configuration is the attribute-name.

>>> conf = Config(key="value")
>>> conf.key
'value'

If a key is not a valid attribute-name in Python,
it will not be accessible using the convenient dot-syntax.
However, values are still accessible using ``getattr``.

>>> conf = Config(**{"bad key": "value"})
>>> getattr(conf, "bad key")
'value'

Indexing Configurations
^^^^^^^^^^^^^^^^^^^^^^^

Every key in the configuration can also be used as an index for the object.
This can be especially useful to avoid more verbose ``getattr`` calls.

>>> conf = Config(**{"a key": "value"})
>>> conf["a key"]
'value'

Tuple indices can be used to get values in hierarchical configuration objects.

>>> conf = Config(**{"sub-conf": {"key": "value"}})
>>> conf["sub-conf", "key"]
'value'

It is also possible to use dot-string indices for hierarchical configurations.

>>> conf = Config(**{"sub-conf": {"key": "value"}})
>>> conf["sub-conf.key"]
'value'

Merging Configurations
^^^^^^^^^^^^^^^^^^^^^^^

Configurations can be merged by means of the "or"-operator, ``|``.

>>> conf1 = Config(key1="foo")
>>> conf2 = Config(key2="bar")
>>> print(conf1 | conf2)
{key1: foo, key2: bar}

Merging is not commutative, so the order of configurations is important.

>>> conf1 = Config(key="val", key1="foo")
>>> conf2 = Config(key="value", key2="bar")
>>> print(conf1 | conf2)
{key: value, key1: foo, key2: bar}
>>> print(conf2 | conf1)
{key: val, key2: bar, key1: foo}

Configurations can also be merged with a ``dict`` (or other mapping).

>>> conf1 = Config(key1="foo")
>>> conf2 = {"key2": "bar"}
>>> print(conf1 | conf2)
{key1: foo, key2: bar}
>>> print(conf2 | conf1)
{key2: bar, key1: foo}

Converting Configurations
^^^^^^^^^^^^^^^^^^^^^^^^^

There are different ways to convert configuration objects to a ``dict`` again.
Non-hierarchical objects can directly be wrapped by the ``dict`` constructor.

>>> conf = Config(key="value")
>>> dict(conf)
{'key': 'value'}

This does not work recursively, however, causing issues with hierarchical objects.
This is where the :func:`~ConfigurationBase.to_dict` method can be useful.

>>> conf = Config(sub={"key": "value"})
>>> dict(conf)
{'sub': PlainConfiguration(key='value')}
>>> conf = Config(sub={"key": "value"})
>>> conf.to_dict()
{'sub': {'key': 'value'}}

Additionally, this method makes it possible to convert a hierarchical objects to a non-nested ``dict``.

>>> conf = Config(sub={"key": "value"})
>>> conf.to_dict(flat=True)
{'sub.key': 'value'}

It is also possible to replace patterns in keys, similar to :func:`~ConfigurationBase.from_dict`.

Overview
^^^^^^^^

.. autosummary::
    :toctree: generated
    :nosignatures:

    ConfigurationBase
    PlainConfiguration
    FrozenConfiguration
    CarefulConfiguration

I/O Utilities
-------------

Configurations are commonly saved in some file to make them accessible outside of the program.
Therefore, upsilonconf provides some convenience function for reading and writing files.
These functions are :func:`load_config` and :func:`save_config`.
These functions make use of a simple, but extensible I/O system
that is built on top of the :class:`io.ConfigIO` interface.
There is also :func:`config_from_cli` to collect configuration values from the CLI.

Convenience Functions
^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: generated
    :nosignatures:

    load_config
    save_config
    config_from_cli

I/O System
^^^^^^^^^^

.. autosummary::
    :toctree: generated
    :nosignatures:

    io.ConfigIO
    io.JSONIO
    io.YAMLIO
    io.TOMLIO
    io.DirectoryIO
    io.ExtensionIO
    io.FlexibleIO