""" A simple configuration library. """

from ._optional_dependency import OptionalDependencyError
from .io import load, save, from_cli
from .config import *

__version__ = "0.4.2.dev1"
__all__ = config.__all__ + [
    "OptionalDependencyError",
    "load_config",
    "save_config",
    "config_from_cli",
]

# aliases
load_config = load
save_config = save
config_from_cli = from_cli
