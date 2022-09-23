""" A simple configuration library. """

from ._import_tricks import _lazy_imports, OptionalDependencyError
from .config import *

__version__ = "0.4.2.dev1"
__all__ = config.__all__ + [
    "OptionalDependencyError",
    "load_config",
    "save_config",
    "config_from_cli",
]

__getattr__, __dir__ = _lazy_imports(
    __package__,
    {"io": ["load", "save"], "cli": ["from_cli"]},
    dir(),
    aliases={"load_config": "load", "save_config": "save", "config_from_cli": "from_cli"}
)
