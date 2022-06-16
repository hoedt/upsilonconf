""" A simple configuration library. """

from ._optional_dependency import OptionalDependencyError
from .io import load, save, from_cli
from .config import *

__version__ = "0.4.1.dev1"
