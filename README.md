# UpsilonConf

UpsilonConf is a simple configuration library written in Python.
It might not be really obvious, but this library is inspired by the great [OmegaConf](https://github.com/omry/omegaconf) library.
OmegaConf is also the backbone for the more advanced [Hydra](https://hydra.cc/) framework.
Concretely, the idea of this library is to provide an alternative to OmegaConf without the overhead of the variable interpolation (especially the `antlr` dependency).
It is also very similar to the (discontinued) [AttrDict](https://github.com/bcj/AttrDict) library.
In the meantime, there is also the [ml_collections](https://github.com/google/ml_collections) library, which seems to build on similar ideas as this project.

Nevertheless, I decided to release upsilonconf because there might be a few features that people might find interesting/useful:
 - dict-like configuration object with attribute access (cf. `attrdict`)
 - hierarchical indexing by means of tuples or *dot-strings* (cf. `omegaconf`)
 - overwriting protection to prevent accidents
 - read from/write to various file formats
 - use hierarchical configs with options (cf. config groups in `hydra`)
 - retrieve and manipulate config using CLI (cf. `omegaconf`)
 - minimal dependencies (cf. `attrdict`)

The name is inspired by OmegaConf.
I decided to go for the Greek letter [Upsilon](https://en.wikipedia.org/wiki/Upsilon) because it is the first letter of [ὑπέρ (hupér)](https://en.wiktionary.org/wiki/ὑπέρ).
This again comes from the fact that this library should mainly help me with managing _hyper_-parameters in neural networks.

### How to Use

```python
import upsilonconf
```

###### creation

```python
conf1 = upsilonconf.load("config.yaml")  # from config file
conf2 = upsilonconf.Configuration(key1="value1", key2=2)  # direct
dictionary = {"sub": conf2}  # sub-configs allowed!
conf3 = upsilonconf.Configuration(**dictionary)  # from dict
conf = conf1 | conf2 | conf3  # from other configurations
```

###### indexing

```python
# getters
conf["key1"] == conf.key1
conf.key2 == conf["sub", "key2"]
conf["sub", "key1"] == conf["sub.key1"]
conf["sub.key2"] == conf.sub.key2

# setters
conf["new_key"] = "new_value"
conf.other_key = "other_value"
conf.sub2 = {"a": .1, "b": 2}
conf["sub2", "c"] = 3.
conf["sub2.d"] = -4

# and deleters...
del conf["sub2.c"]
```

###### overwrite protection

```python
try:
    conf["key1"] = "overwrite1"
except ValueError:
    print("overwriting")
    conf.overwrite("key1", "overwrite1")

try:
    conf.key1 = "overwrite2"
except AttributeError:
    print("overwriting")
    conf.overwrite("key1", "overwrite2")

try:
    conf.update(key1="overwrite3")
except ValueError:
    print("overwriting")
    conf.overwrite_all(key1="overwrite3")
```

###### flexible I/O

```python
# different file formats (with optional requirements)
conf = upsilonconf.load("config.yaml")  # with patched float parsing
upsilonconf.save(conf, "config.json")  # with indentation by default

# organise hierarchical configs in directories
upsilonconf.save({"key": "option1"}, "config_dir/config.json")
upsilonconf.save({"foo": 1, "bar": 2}, "config_dir/key/option1.json")
upsilonconf.save({"foo": 2, "baz": 3}, "config_dir/key/option2.json")

# load arbitrary parts of hierarchy
conf = upsilonconf.load("config_dir/key")
conf == upsilonconf.Configuration(
    option1={"foo": 1, "bar": 2}, 
    option2={"foo": 2, "baz": 3}
)

# hierarchies enable option feature
conf = upsilonconf.load("config_dir")
conf == upsilonconf.Configuration(key={"foo": 1, "bar": 2})

# store hierarchy to default file in specified directory
upsilonconf.save(conf, "backup")
```

###### CLI helper

```python
# read command-line arguments (from sys.argv)
conf = upsilonconf.from_cli()

# parse arbitrary arguments to construct config
conf = upsilonconf.from_cli(["key=1", "sub.test=2"])
conf == Configuration(key=1, sub={"test": 2})

# use file as base config
conf = upsilonconf.from_cli(["--config", "config.yaml", "key=1", "sub.test=2"])
result = upsilonconf.load("config.yaml")
result.overwrite_all(key=1, sub={"test": 2})
conf == result

# enhance existing argparser
from argparse import ArgumentParser
parser = ArgumentParser()
# add other arguments...
conf, args = upsilonconf.from_cli(parser=parser)
```
