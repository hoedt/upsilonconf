# UpsilonConf

UpsilonConf is a simple configuration library written in Python.

A few features that you might find interesting/useful:
 - dict-like configuration object with attribute access (cf. `attrdict`)
 - hierarchical indexing by means of tuples or *dot-strings* (cf. `omegaconf`)
 - read from/write to various file formats
 - use hierarchical configs with options (cf. config groups in `hydra`)
 - retrieve and manipulate config using CLI (cf. `omegaconf`)
 - minimal dependencies (cf. `attrdict`)
 - configs with overwriting protection to prevent unexplainable bugs

[![pypi badge](https://img.shields.io/pypi/v/upsilonconf?label=PyPI)](https://pypi.org/project/upsilonconf)
[![conda badge](https://img.shields.io/conda/v/hoedt/upsilonconf)](https://anaconda.org/hoedt/upsilonconf)
[![docs badge](https://img.shields.io/github/actions/workflow/status/hoedt/upsilonconf/sphinx.yml?branch=main&label=docs&logo=github)](https://hoedt.github.io/upsilonconf)
[![licencse badge](https://img.shields.io/github/license/hoedt/upsilonconf)](https://github.com/hoedt/upsilonconf/blob/main/LICENSE)

---

### How to install

Using `pip` to install from PyPI:

```shell
python -m pip install upsilonconf
```

Optional dependencies (e.g. `pyyaml`) can be included using

```shell
python -m pip install upsilonconf[YAML]
```

Using `conda` to install from Anaconda:

```shell
conda install hoedt::upsilonconf
```

Optional dependencies (e.g. `pyyaml`) have to be installed separately.

---

### How to Use

```python
>>> import upsilonconf
>>> from upsilonconf import PlainConfiguration as Configuration
```

###### Creation

load config from file

```python
>>> conf = upsilonconf.load("my_config.yml")
```

or directly create config object

```python
>>> conf = Configuration(key1="value1", sub={"key1": 1, "key2": 2})
```

###### Indexing

Access values the way you like

```python
>>> assert conf["key1"] == conf.key1
>>> assert conf.sub.key2 == conf["sub", "key2"]
>>> assert conf["sub", "key1"] == conf["sub.key1"]
>>> assert conf["sub.key2"] == conf.sub.key2
```

###### Cool Tricks

unpack configurations to function arguments

```python
>>> def test(key1, key2):
...    return key1 + key2
>>> test(**conf.sub)
3
```

convert config to flat `dict`

```python
>>> conf.to_dict(flat=True)
{'key1': 'value1', 'sub.key1': 1, 'sub.key2': 2}
```

merge configurations with `|`

```python
>>> merged = conf | {"sub.key2": 3, "sub.key3": 2}
>>> merged.sub.key2
3
>>> merged.sub.key3
2
```

More details can be found in the [documentation](https://hoedt.github.io/upsilonconf)

###### flexible I/O

support for different file formats

```python
>>> conf = upsilonconf.load("config.yaml")  # with patched float parsing
>>> upsilonconf.save(conf, "config.json")  # with indentation by default
```

transform non-identifier keys in files on-the-fly

```python
>>> conf = upsilonconf.load("config.yaml", key_mods={" ": "_"})
>>> upsilonconf.save(conf, "config.json", key_mods={"_": " "})
```

organise hierarchical configs in directories

```python
>>> upsilonconf.save({"key": "option1"}, "config_dir/config.json")
>>> upsilonconf.save({"foo": 1, "bar": 2}, "config_dir/key/option1.json")
>>> upsilonconf.save({"foo": 2, "baz": 3}, "config_dir/key/option2.json")
```

load arbitrary parts of hierarchy

```python
>>> conf = upsilonconf.load("config_dir/key")
>>> conf == Configuration(
...     option1={"foo": 1, "bar": 2},
...     option2={"foo": 2, "baz": 3}
... )
```

hierarchies enable option feature

```python
>>> conf = upsilonconf.load("config_dir")
>>> conf == Configuration(key={"foo": 1, "bar": 2})
```

store hierarchy to directory with a default file format

```python
>>> upsilonconf.save(conf, "backup")
```

###### CLI helper

read command-line arguments

```python
>>> conf = upsilonconf.from_cli()
```

parse arbitrary arguments to construct config

```python
>>> conf = upsilonconf.from_cli(["key=1", "sub.test=2"])
>>> assert conf == Configuration(key=1, sub={"test": 2})
```

use file as base config

```python
>>> conf = upsilonconf.from_cli(["--config", "config.yaml", "key=1", "sub.test=2"])
>>> result = upsilonconf.load("config.yaml")
>>> result.overwrite_all(key=1, sub={"test": 2})
>>> assert conf == result
```

enhance existing argparser

```python
>>> from argparse import ArgumentParser
>>> parser = ArgumentParser()
>>> # add other arguments...
>>> conf, args = upsilonconf.from_cli(parser=parser)
```

### Feedback

This library is very much a work in progress.
I welcome any feedback, especially in shaping the interface.
Of course, also bug reports and feature requests are very useful feedback.
Just create an [issue](https://github.com/hoedt/upsilonconf/issues) on github.

