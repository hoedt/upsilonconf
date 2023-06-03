""" A simple configuration library. """

from .config import *
from .io import *

__version__ = "0.7.0"
__all__ = config.__all__ + [  # type: ignore  # https://github.com/python/mypy/issues/10967
    "OptionalDependencyError",
    "load_config",
    "save_config",
    "config_from_cli",
]

# aliases
load = load_config
save = save_config
config_from_cli = from_cli
