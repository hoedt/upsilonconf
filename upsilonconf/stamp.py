from collections.abc import Sequence
from typing import Any, Dict, Hashable

from .base import ConfigurationBase


def _assure_hashable(o: Any) -> Hashable:
    try:
        if hash(o) is not None:
            return o
    except TypeError:
        pass

    if isinstance(o, ConfigurationBase):
        return ConfigurationStamp(o)
    elif isinstance(o, Sequence):
        return tuple(_assure_hashable(i) for i in o)
    else:
        raise ValueError(f"unhashable value in config: '{o!r}'")


class ConfigurationStamp(ConfigurationBase, Hashable):
    def __init__(self, config: ConfigurationBase):
        super().__init__(**{str(k): _assure_hashable(v) for k, v in config.items()})

    def __copy__(self) -> "ConfigurationStamp":
        return self

    def __deepcopy__(self, memo: Dict = None) -> "ConfigurationStamp":
        return self

    def __hash__(self) -> int:
        # inspired by https://stackoverflow.com/questions/20832279
        h = len(self)
        for k, v in self.items():
            hx = hash((hash(k), hash(v)))
            h ^= (hx ^ 0x055b_4db3 ^ (hx << 16)) * 4_155_791_671
            h &= 0xffff_ffff_ffff_ffff

        return h
