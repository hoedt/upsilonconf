""" A simple configuration library. """

from .config import *
from .io import *

__version__ = "0.5.1"
__all__ = config.__all__ + [
    "OptionalDependencyError",
    "load_config",
    "save_config",
    "config_from_cli",
]

# aliases
load = load_config
save = save_config
config_from_cli = from_cli
