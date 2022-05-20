""" A simple configuration library. """

from .utils.optional_dependency import OptionalDependencyError
from .io import load, save
from .config import *

__version__ = "0.3.0.dev1"
