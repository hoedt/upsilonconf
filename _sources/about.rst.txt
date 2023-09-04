
Fun Facts
=========

.. contents::
    :local:

Origins
-------

For a DL course that I created, I was looking for a configuration library.
Because I wanted their experience to generalise to future projects,
I looked for commonly used configuration libraries.
Back in those days, `Hydra`_ appeared to be the most popular.
When I realised `OmegaConf`_ was the actual configuration library,
I thought it would be a good idea to design the code around omegaconf.

Generally, I liked the idea behind omegaconf as a configuration library,
but in the end I stumbled over a few (minor) details.
First of all, omegaconf depends on `antlr` to provide variable interpolations,
which is a feature I do not really care for.
Secondly, when digging into the code of omegaconf,
I realised I did not quite like its software design.

Eventually, I decided to write something by myself for my students.
On one side not to bloat their python installation with (unnecessary) dependencies.
On the other side, I wanted to promote good software design principles.

After some years of teaching, I decided there might be value in publishing this code.
I could have just dropped the code on Github and be done with it.
However, I thought it would be a fun exercise to create a proper package.
Therefore, Upsilonconf can be considered an exercise in package design/management.

The package name is inspired by OmegaConf because this is where the story started.
I decided to swap out the Greek prefix with `Upsilon`_, which is the first letter of `ὑπέρ (hupér)`_.
After all, this library is mainly intended to help with _hyper_-parameters in DL.

.. _Upsilon: https://en.wikipedia.org/wiki/Upsilon
.. _ὑπέρ (hupér): https://en.wikipedia.org/wiki/Upsilon

Design Principles
-----------------

In order to understand why a feature has (not) been implemented,
it can be useful to understand some of the underlying principles.
You do not have to agree or adhere to these principles if you do not want.
They are merely here to help you understand the library better.

Software
^^^^^^^^

Some principles behind the code.

 1. Upsilonconf is supposed to be **minimal**.
    Not in the sense of character count in code, but rather from a technical standpoint.
    On one side, the goal is to have as little requirements as possible.
    On the other side, this library should do only one thing, but do it well, cf. the `Unix Philosophy`_.
    Note that this does not mean that new features are not welcome!
 2. The code has been written with `coupling`_ and `cohesion`_ in mind.
    The goal is that every component in this library should be easily adaptable.
    This should make it easier to extend the library and/or change how things are done.
    However, ideally this also makes it easier to start or stop using this package.
    This is also reflected in how I think about configurations (see other sub-section).
 3. The code aims to provide useful **typing**.
    Type hints in Python make it possible to have (some) type checks before running the code.
    This typically helps to find errors before having to run any code.
    Therefore, upsilonconf aims to provide as much type hints as possible.
    Ideally, configuration objects would have type hints for configuration values.
    However, at the time of writing, this only seems to be possible through `dataclasses`_.
 4. The code is being developed using a (relaxed) **test-driven** approach.
    Rather than just implementing a feature or a fix to some code,
    there should also be a unit test that fails without the feature or fix.
    In this sense, the tests define the expected/desired behaviour.
    This also means that in case of any disputes what code is supposed to do,
    we should be able to fall back to the unit tests.
 5. Finally, the `Zen of Python`_ might be a good summary of what all of the above points aim to do.
    Feel free to let me know if you think upsilonconf is not conforming to one of these rules.

.. _Unix Philosophy: https://en.wikipedia.org/wiki/Unix_philosophy
.. _cohesion: https://en.wikipedia.org/wiki/Cohesion_(computer_science)
.. _coupling: https://en.wikipedia.org/wiki/Coupling_(computer_programming)
.. _dataclasses: https://docs.python.org/3/library/dataclasses.html
.. _Zen of Python: https://peps.python.org/pep-0020/

Configurations
^^^^^^^^^^^^^^

Some principles on using configuration files in general

 1. Configuration files are **not the same** as configuration objects.
    Configuration libraries are typically bound to file formats.
    Moreover, some libraries introduce additional syntax.
    E.g. `OmegaConf`_ introduces variable interpolation syntax to YAML.
    Although the variable interpolation syntax can be useful,
    it practically defines a new configuration file format.
    This should not be the job of a configuration library.
    After all, this couples the configuration library to the file format.
    Upsilonconf aims to provide an object that is convenient to work with.
    Furthermore, it is possible to read from/write to any format you like.
 2. Code should be configured in a way that does **not require value duplication**.
    If you feel like you need to repeat configuration values,
    I would argue that you are configuring your code in the wrong way.
    For me, the main goal of configuration files is
    to conveniently transfer information from the outside world into the code.
    Examples that argue in favour of variable interpolation typically ignore this aspect.
    Either information is (unnecessarily) duplicated,
    e.g. ``{base: foo/bar, path: ${base}/file}`` (using `OmegaConf`_ syntax)
    could easily be replaced by ``{base: foo/bar, filename: file}``.
    This does not directly affect upsilonconf, but hopefully serves as food for thought.
 3. Configuration objects should not be used as **arguments to functions**.
    Some people like to use `dataclasses`_ as configuration objects.
    However, this typically requires functions to take these dataclasses as arguments.
    Technically, this works great because you can pack all arguments in one object.
    However, there are a few disadvantages to this approach.
    First of all, function signatures are no longer self-explanatory.
    Furthermore, code depends on the configuration object (increased `coupling`_).
    Finally, it invites to increase the number of arguments a function takes.
    A large number of arguments is one of those code smells that might indicate high `coupling`_.
    Therefore, I personally prefer not to pass configuration objects as arguments.
    Instead, values should be extracted from the configuration object and passed to the function.
    This is exactly what the ``dict`` interface of upsilonconf objects allows you to do.

Related Libraries
-----------------

This is not the first and probably also not the last configuration library.
There are also some libraries that happen to provide similar features.
If you are not sure whether upsilonconf is what you are looking for,
you might find an alternative that fits your requirements in the list(s) below.
However, feel free to submit a `feature request`_ if you believe something is missing in upsilonconf.

.. _feature request: https://github.com/hoedt/upsilonconf/issues/new

ML Configuration Libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^

 - `OmegaConf`_ is a configuration library from Facebook.
   It is probably best known as the configuration library behind `Hydra`_.
 - `ml_collections`_ is a configuration library from Google.
   This library has been used e.g. for the `Big Vision`_ (vision transformers) research.

.. _OmegaConf: https://omegaconf.readthedocs.io
.. _ml_collections: https://ml-collections.readthedocs.io
.. _Hydra: https://hydra.cc
.. _Big Vision: https://github.com/google-research/big_vision

Configuration File Formats
^^^^^^^^^^^^^^^^^^^^^^^^^^

 - Javascript Object Notation `(JSON) <https://www.json.org>`_ is commonly used on the web.
   Python comes with the `json`_ library for reading and writing JSON files by default.
 - YAML Ain't Markup Language `(YAML) <https://yaml.org>`_ is a popular configuration format.
   The default library in Python seems to be `PyYAML`_, which supports YAML 1.1.
   There is also the `ruamel.yaml`_ package for YAML 1.2 support.
   Pyyaml has this annoying bug that e.g. ``1e-3`` is parsed as string instead of float.
   Upsilonconf uses ``pyyaml`` as optional dependency for YAML I/O, but patches this bug.
 - Tom's Obvious Minimal Language `(TOML) <https://toml.io>`_ is an increasingly popular configuration format.
   Since Python 3.11, Python comes with the `tomllib`_ library for reading TOML files.
   Writing is possible using the `Tomli-W`_ or `TOML Kit`_ (or other) packages.
   Upsilonconf uses ``tomlkit`` as optional dependency for TOML I/O.
 - Bespoken Object Notation `(BespON) <https://bespon.org/>`_ is a more opinionated configuration format.
   The reference implementation is provided in the `BespON`_ package.
   The dot-separated indices in Upsilonconf can also be found in the BespON specification.
   At the time of writing, upsilonconf does not support BespON files out of the box.
 - INItialisation files `(INI) <https://en.wikipedia.org/wiki/INI_file>`_ are MS-DOS configuration files.
   The `configparser`_ library in Python is able to read and write INI files.
   INI can be considered the predecessor of TOML.
   At the time of writing, upsilonconf does not support INI files out of the box.
 - Python scripts with variable definitions can also be used as configuration file.
   These configuration files are `Turing complete`_ and can therefore do anything.
   Upsilonconf is not Turing complete by design, but it could be used in this style of config.
 - ...

.. _json: https://docs.python.org/3/library/json.html
.. _tomllib: https://docs.python.org/3/library/tomllib.html
.. _configparser: https://docs.python.org/3/library/configparser.html
.. _PyYAML: https://pypi.org/project/PyYAML/
.. _ruamel.yaml: https://pypi.org/project/ruamel.yaml/
.. _Tomli-W: https://pypi.org/project/tomli-w
.. _TOML Kit: https://pypi.org/project/tomlkit
.. _BespON: https://pypi.org/project/BespON/
.. _Turing complete: https://en.wikipedia.org/wiki/Turing_completeness
