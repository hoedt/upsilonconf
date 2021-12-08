import io
import os
import unittest
from pathlib import Path
from unittest import TestCase
from unittest import mock

from upsilonconf.config import Configuration
from upsilonconf.serialisation.persistence import load, save
from upsilonconf.serialisation.persistence import yaml_load


CONFIG = Configuration(foo=1, bar="test", baz={"a": 0.1, "b": 0.2})
CONFIG_JSON_LINES = (
    "{",
    '  "foo": 1,',
    '  "bar": "test",',
    '  "baz": {',
    '    "a": 0.1,',
    '    "b": 0.2',
    "  }",
    "}",
)
CONFIG_YAML_LINES = (
    "foo: 1",
    "bar: test",
    "baz:",
    "  a: 0.1",
    "  b: 0.2",
)


class TestFileOperations(TestCase):
    def test_save_json(self):
        path = Path.home() / "test.json"

        m_open = mock.mock_open()
        buffer = io.StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch("upsilonconf.serialisation.persistence.open", m_open):
            save(CONFIG, path)

        m_open.assert_called_once_with(path, "r")
        buffer.seek(0)
        for expected, truth in zip(CONFIG_JSON_LINES, buffer):
            self.assertEqual(expected, truth.rstrip())

    def test_load_json(self):
        path = Path.home() / "test.json"

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_JSON_LINES))
        with mock.patch("upsilonconf.serialisation.persistence.open", m_open):
            c = load(path)

        self.assertEqual(CONFIG, c)

    def test_save_yaml(self):
        path = Path.home() / "test.yaml"

        m_open = mock.mock_open()
        buffer = io.StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch("upsilonconf.serialisation.persistence.open", m_open):
            save(CONFIG, path)

        m_open.assert_called_once_with(path, "r")
        buffer.seek(0)
        for expected, truth in zip(CONFIG_YAML_LINES, buffer):
            self.assertEqual(expected, truth.rstrip())

    def test_load_yaml(self):
        path = Path.home() / "test.yaml"

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_YAML_LINES))
        with mock.patch("upsilonconf.serialisation.persistence.open", m_open):
            c = load(path)

        self.assertEqual(CONFIG, c)

    def test_load_yaml_float(self):
        c = yaml_load(io.StringIO("foo: 1.3e-5"))
        self.assertEqual(1.3e-5, c["foo"])
        c = yaml_load(io.StringIO("foo: 1e5"))
        self.assertEqual(1e5, c["foo"])
        c = yaml_load(io.StringIO("foo: .5e3"))
        self.assertEqual(0.5e3, c["foo"])

    @unittest.skip("TODO: specify behaviour")
    def test_save_dir(self):
        path = Path.home()
        self.fail()

    @unittest.skip("TODO: specify behaviour")
    def test_load_dir(self):
        path = Path.home()
        self.fail()

    def test_save_bad_extension(self):
        path = Path.home() / "test.invalid"
        with self.assertRaisesRegex(ValueError, "extension"):
            save(CONFIG, path)

    def test_load_bad_extension(self):
        path = Path.home() / "test.invalid"
        with self.assertRaisesRegex(ValueError, "extension"):
            load(path)
