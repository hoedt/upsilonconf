
Getting Started
===============

On this page, you should be able to find everything necessary to get you going.

.. contents::
    :local:

Installation
------------

The only pre-requisite for installing UpsilonConf is a working `Python`_ installation.
Any version since Python 3.6 should work.
If you wish to read/write certain configuration file formats,
you might want to install one or more of the optional dependencies.

Conda
^^^^^

To install the `Anaconda`_ package with ``conda``, you would run the following command in your terminal:

.. code-block:: shell

    conda install hoedt::upsilonconf

The ``::``-syntax allows to specify the channel without prioritising it over the default channel.

If you want to interact with configurations stored in YAML or TOML files, you can simply append the corresponding library to the previous command.

.. code-block:: shell

    conda install hoedt::upsilonconf pyyaml tomlkit

Pip
^^^

To install the `PyPi`_ package with ``pip``, you would enter the following in your terminal:

.. code-block:: shell

    python -m pip install upsilonconf

Optional dependencies can be installed using the `extras`_ syntax:

.. code-block:: shell

    python -m pip install upsilonconf[YAML]

or:

.. code-block:: shell

    python -m pip install upsilonconf[TOML]

.. note:: Since Python 3.11, ``tomlkit`` is no longer needed if you only want to **read TOML files**.

.. _Python: https://www.python.org/
.. _Anaconda: https://anaconda.org/hoedt/upsilonconf
.. _PyPI: https://pypi.org/project/upsilonconf/
.. _extras: https://peps.python.org/pep-0508/#extras

------

Quickstart
----------

.. currentmodule:: upsilonconf

Before you can use any package, you have to import it:

.. doctest::

    >>> import upsilonconf

This should give you access to all of the functionality this package has to offer.


How to create configuration objects?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are multiple ways to create configuration objects in UpsilonConf.
The most direct one is to specify key-value pairs as keyword arguments to the constructor:

.. doctest::

    >>> conf = upsilonconf.Configuration(sep="\t", file=None, flush=True)
    >>> print(conf)
    ... {}

If you happen to have a ``dict`` with key-value pairs already, you can use the constructor as follows:

.. doctest::

    >>> dictionary = {"sep": "\t", "file": None, "flush": True}
    >>> conf = upsilonconf.Configuration(**dictionary)
    >>> print(conf)
    ... {}

This should also work for other `mapping`_ types.

Note that when a value is of type ``dict`` (or any other `mapping`_),
it will automatically be converted to a *hierarchical* configuration object:

.. doctest::

    >>> conf = upsilonconf.Configuration(content="hello world", options=dictionary)
    >>> print(conf)
    ... {}

However, often the most convenient way is to read the configuration from some file.
This can be done by means of the :func:`load_config` function:::

    >>> upsilonconf.load_config("config.json")
    ... {}

Other file formats are also supported if the corresponding (optional) dependencies are installed.

.. _mapping: https://docs.python.org/3/glossary.html#term-mapping

How to access values?
^^^^^^^^^^^^^^^^^^^^^

There are also multiple ways to access the values that are stored in a configuration.
The first option is to use the corresponding key as attribute name:

.. doctest::

    >>> conf.content
    ... "hello world"

Alternatively, the key can be used as an index for the configuration:

.. doctest::

    >>> conf["content"]
    ... "hello world"

This also works for hierarchical configuration objects:

.. doctest::

    >>> conf.options.sep
    ... "\t"
    >>> conf["options"]["sep"]
    ... "\t"

Moreover, hierarchical indices can also be given as ``tuple`` or ``.``-separated strings:

.. doctest::

    >>> conf["options", "sep"]
    ... "\t"
    >>> conf["options.sep"]
    ... "\t"

All of these access modes also work for setting or modifying values (if the configuration is writeable).
