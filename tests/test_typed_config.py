from unittest import TestCase

from upsilonconf.config import PlainConfiguration


class TypedSubConfiguration(PlainConfiguration):
    a: float = 0.1
    b: float = 0.2


class TypedConfiguration(PlainConfiguration):
    foo: int
    bar: str = "test"
    baz: TypedSubConfiguration = TypedSubConfiguration()


class TestTypedConfiguration(TestCase):
    def setUp(self):
        self.simple_config = TypedSubConfiguration()
        self.complex_config = TypedConfiguration(
            foo=69, bar="test", sub=self.simple_config
        )
