""" A simple configuration library. """

from .config import *

__version__ = "0.4.2.dev1"
__all__ = config.__all__ + [
    "OptionalDependencyError",
    "load_config",
    "save_config",
    "config_from_cli",
]


def __getattr__(name: str):
    import importlib

    if name == "load" or name == "load_config":
        return importlib.import_module(".io", __package__).load
    elif name == "save" or name == "save_config":
        return importlib.import_module(".io", __package__).save
    elif name == "from_cli" or name == "config_from_cli":
        return importlib.import_module(".io", __package__).from_cli
    elif name == "OptionalDependencyError":
        return importlib.import_module(
            "._optional_dependency", __package__
        ).OptionalDependencyError

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__():
    yield from __all__
    yield from ("load", "save", "from_cli")
