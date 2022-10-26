from io import StringIO
from unittest import mock

from upsilonconf.config import InvalidKeyError
from upsilonconf.io.toml import *
from .test_base import Utils


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

    def test_load_config_whitespace_key(self):
        file_contents = self.file_contents.replace("foo", "'space foo'")
        m_open = mock.mock_open(read_data=file_contents)
        with self.assertRaises(InvalidKeyError):
            with mock.patch("upsilonconf.io.base.open", m_open):
                self.io.load_config(self.file_path)

    def test_read_from_whitespace_key(self):
        buffer = StringIO(self.file_contents.replace("foo", "'space foo'"))
        data = self.io.read_from(buffer)
        ref = {("space " + k if k == "foo" else k): v for k, v in Utils.CONFIG.items()}
        self.assertDictEqual(ref, dict(data))

    def test_write_to_whitespace_key(self):
        buffer = StringIO()
        self.io.write_to(
            buffer,
            {("space " + k if k == "foo" else k): v for k, v in Utils.CONFIG.items()},
        )
        buffer.seek(0)
        ref = self.file_contents.replace("foo", '"space foo"')
        self.assertMultiLineEqual(ref, buffer.getvalue().rstrip())
