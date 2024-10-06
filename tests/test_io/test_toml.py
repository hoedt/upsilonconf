from io import StringIO
from unittest import mock

from upsilonconf.io.toml import *
from .test_base import Utils, deprecated


class TestTOMLIO(Utils.TestConfigIO):
    @staticmethod
    def generate_file_content():
        yield "foo = 1"
        yield 'bar = "test"'
        yield ""
        yield "[baz]"
        yield "a = 0.1"
        yield "b = 0.2"

    @staticmethod
    def default_io():
        return TOMLIO()

    def test_extensions(self):
        self.assertIn(".toml", self.io.extensions)

    def test_parse_value_map(self):
        data = self.io.parse_value("{a = 4, b = 2}")
        self.assertDictEqual(data, {"a": 4, "b": 2})

    @deprecated
    def test_load_config_whitespace_key(self):
        file_contents = self.file_contents.replace("foo", "'space foo'")
        m_open = mock.mock_open(read_data=file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            self.io.load_config(self.file_path)

    def test_read_from_whitespace_key(self):
        buffer = StringIO(self.file_contents.replace("foo", "'space foo'"))
        data = self.io.read_from(buffer)
        ref = Utils.CONFIG.to_dict(key_mods={"foo": "space foo"})
        self.assertDictEqual(ref, dict(data))

    def test_write_to_whitespace_key(self):
        buffer = StringIO()
        d = Utils.CONFIG.to_dict(key_mods={"foo": "space foo"})
        self.io.write_to(buffer, d)
        buffer.seek(0)
        ref = self.file_contents.replace("foo", '"space foo"')
        self.assertMultiLineEqual(ref, buffer.getvalue().rstrip())
