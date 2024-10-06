import os
from io import StringIO
from pathlib import Path
from unittest import TestCase, mock

from upsilonconf import ConfigurationBase, PlainConfiguration
from upsilonconf.io.directory import *
from upsilonconf.io.json import JSONIO
from upsilonconf.io.yaml import YAMLIO
from upsilonconf.io.base import ExtensionIO
from .test_base import Utils, deprecated


def fake_directory_structure(root, paths):
    root = Path(root)

    class _MockedScandirIterator:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def __iter__(self):
            yield from (PlainConfiguration(name=sub) for sub in paths)

    def decorator(func):
        @mock.patch("upsilonconf.io.base.Path.exists")
        @mock.patch("upsilonconf.io.base.Path.is_dir")
        @mock.patch("upsilonconf.io.base.Path.iterdir")
        def wrapper(*args, **kwargs):
            *og_args, m_iterdir, m_is_dir, m_exists = args
            with mock.patch("pathlib._normal_accessor.scandir") as m_scandir:
                m_is_dir.side_effect = lambda p: p == root
                m_exists.side_effect = lambda p: p.file_name in paths
                m_scandir.return_value = _MockedScandirIterator()
                m_iterdir.return_value = (root / sub for sub in paths)
                func(*og_args, **kwargs)

        return wrapper

    return decorator


class TestDirectoryIO(TestCase):
    path = Path.cwd()

    @staticmethod
    def main_file_content():
        yield from Utils.DEFAULT_LINES

    @staticmethod
    def option_file_content():
        yield "{"
        yield '  "foo": "bar",'
        yield '  "bar": "value",'
        yield '  "baz": "other"'
        yield "}"

    @classmethod
    def setUpClass(cls):
        cls.file_contents = os.linesep.join(cls.main_file_content())

    def setUp(self):
        self.io = DirectoryIO(JSONIO())

    def test_extensions(self):
        self.assertIn("", self.io.extensions)

    def test_constructor(self):
        io = DirectoryIO(JSONIO())
        self.assertEqual(DirectoryIO.DEFAULT_NAME + ".json", io.file_name)

    def test_constructor_main_file(self):
        io = DirectoryIO(JSONIO(), main_file="test.json")
        self.assertEqual("test.json", io.file_name)

    def test_constructor_main_file_no_extension(self):
        io = DirectoryIO(JSONIO(), main_file="test")
        self.assertEqual("test.json", io.file_name)

    def test_constructor_main_file_unsupported_extension(self):
        with self.assertRaises(ValueError):
            DirectoryIO(JSONIO(), main_file="config.yaml")

    def test_read_from(self):
        with self.assertRaises(TypeError):
            self.io.read_from(StringIO())

    def test_parse_value_bool(self):
        self.assertTrue(self.io.parse_value("true"))
        self.assertFalse(self.io.parse_value("false"))

    def test_parse_value_int(self):
        self.assertEqual(42, self.io.parse_value("42"))

    def test_parse_value_float(self):
        pi = self.io.parse_value("3.1415")
        self.assertEqual(3.1415, pi)
        sc = self.io.parse_value("1e-6")
        self.assertEqual(1e-6, sc)

    def test_parse_value_str(self):
        data = self.io.parse_value('"some string"')
        self.assertEqual(data, "some string")

    def test_parse_value_seq(self):
        data = self.io.parse_value("[1, 2, 3]")
        self.assertSequenceEqual(data, [1, 2, 3])

    def test_parse_value_map(self):
        data = self.io.parse_value('{"a": 4, "b": 2}')
        self.assertDictEqual(data, {"a": 4, "b": 2})

    def test_parse_value_error(self):
        with self.assertRaises(ValueError):
            self.io.parse_value("}bla\nbla{")

    @fake_directory_structure(path, ["config.json"])
    def test_read(self):
        m_open = mock.mock_open(read_data=self.file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            data = self.io.read(self.path)

        m_open.assert_called_once_with(self.path / "config.json", "r", encoding="utf-8")
        self.assertDictEqual(dict(Utils.CONFIG), dict(data))

    @fake_directory_structure(path, ["config.yaml"])
    def test_read_non_default(self):
        io = DirectoryIO(ExtensionIO(JSONIO(), YAMLIO()))
        assert io.config_io.default_ext == ".json", "invalid test setup"

        m_open = mock.mock_open(read_data=self.file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            data = io.read(self.path)

        m_open.assert_called_once_with(self.path / "config.yaml", "r", encoding="utf-8")
        self.assertDictEqual(dict(Utils.CONFIG), dict(data))

    @fake_directory_structure(path, ["config.json", "sub1.json", "sub2.json"])
    def test_read_multiple(self):
        m_open = mock.mock_open(read_data=self.file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            data = self.io.read(self.path)

        m_open.assert_has_calls(
            [
                mock.call(self.path / "config.json", "r", encoding="utf-8"),
                mock.call(self.path / "sub1.json", "r", encoding="utf-8"),
                mock.call(self.path / "sub2.json", "r", encoding="utf-8"),
            ],
            any_order=True,
        )
        self.assertEqual(3, m_open.call_count)
        ref = dict(Utils.CONFIG, sub1=Utils.CONFIG, sub2=Utils.CONFIG)
        self.assertDictEqual(ref, dict(data))

    @fake_directory_structure(path, ["sub1.json", "sub2.json"])
    def test_read_without_base(self):
        m_open = mock.mock_open(read_data=self.file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            data = self.io.read(self.path)

        m_open.assert_has_calls(
            [
                mock.call(self.path / "sub1.json", "r", encoding="utf-8"),
                mock.call(self.path / "sub2.json", "r", encoding="utf-8"),
            ],
            any_order=True,
        )
        self.assertEqual(2, m_open.call_count)
        ref = dict(sub1=Utils.CONFIG, sub2=Utils.CONFIG)
        self.assertDictEqual(ref, dict(data))

    @fake_directory_structure(path, ["config.json", "foo.json"])
    def test_read_options(self):
        file_contents = os.linesep.join(self.option_file_content())
        m_open = mock.mock_open(read_data=file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            data = self.io.read(self.path)

        m_open.assert_has_calls(
            [
                mock.call(self.path / "config.json", "r", encoding="utf-8"),
                mock.call(self.path / "foo.json", "r", encoding="utf-8"),
            ],
            any_order=True,
        )
        self.assertEqual(2, m_open.call_count)
        ref = dict(foo="value", bar="value", baz="other")
        self.assertDictEqual(ref, dict(data))

    @fake_directory_structure(path, ["config.json", "bar.json"])
    def test_read_options_bad(self):
        file_contents = os.linesep.join(self.option_file_content())
        m_open = mock.mock_open(read_data=file_contents)
        with self.assertRaisesRegex(ValueError, "bar.json"):
            with mock.patch("upsilonconf.io.base.open", m_open):
                self.io.read(self.path)

    @deprecated
    @fake_directory_structure(path, ["config.json", "sub1.json", "sub2.json"])
    def test_load_config(self):
        m_open = mock.mock_open(read_data=self.file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            config = self.io.load_config(self.path)

        m_open.assert_has_calls(
            [
                mock.call(self.path / "config.json", "r", encoding="utf-8"),
                mock.call(self.path / "sub1.json", "r", encoding="utf-8"),
                mock.call(self.path / "sub2.json", "r", encoding="utf-8"),
            ],
            any_order=True,
        )
        self.assertEqual(3, m_open.call_count)
        self.assertIsInstance(config, ConfigurationBase)
        ref = PlainConfiguration(**Utils.CONFIG, sub1=Utils.CONFIG, sub2=Utils.CONFIG)
        self.assertEqual(ref, config)

    @deprecated
    @fake_directory_structure(path, ["config.json", "sub1.json", "sub2.json"])
    def test_load_config_key_mods(self):
        good, bad = "a", "A"
        assert any(good in k for k in Utils.CONFIG.keys()), "invalid test setup"
        assert not any(
            good in v if isinstance(v, str) else good == str(v)
            for v in Utils.CONFIG.values()
        ), "invalid test setup"
        m_open = mock.mock_open(read_data=self.file_contents.replace(good, bad))
        with mock.patch("upsilonconf.io.base.open", m_open):
            config = self.io.load_config(self.path, key_mods={bad: good})

        m_open.assert_has_calls(
            [
                mock.call(self.path / "config.json", "r", encoding="utf-8"),
                mock.call(self.path / "sub1.json", "r", encoding="utf-8"),
                mock.call(self.path / "sub2.json", "r", encoding="utf-8"),
            ],
            any_order=True,
        )
        self.assertEqual(3, m_open.call_count)
        self.assertIsInstance(config, ConfigurationBase)
        ref = PlainConfiguration(**Utils.CONFIG, sub1=Utils.CONFIG, sub2=Utils.CONFIG)
        self.assertEqual(ref, config)

    def test_write_to(self):
        with self.assertRaises(TypeError):
            self.io.write_to(StringIO(), Utils.CONFIG)

    def test_write(self):
        m_open = mock.mock_open()
        buffer = StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch("upsilonconf.io.base.open", m_open):
            self.io.write(dict(Utils.CONFIG), self.path)

        m_open.assert_called_once_with(self.path / "config.json", "w", encoding="utf-8")
        buffer.seek(0)
        for expected in self.main_file_content():
            self.assertEqual(expected, next(buffer).rstrip())

    def test_write_config(self):
        m_open = mock.mock_open()
        buffer = StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            self.io.write(Utils.CONFIG, self.path)

        m_open.assert_called_once_with(self.path / "config.json", "w", encoding="utf-8")
        buffer.seek(0)
        for expected in self.main_file_content():
            self.assertEqual(expected, next(buffer).rstrip())

    @deprecated
    def test_save_config(self):
        m_open = mock.mock_open()
        buffer = StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            self.io.save_config(Utils.CONFIG, self.path)

        m_open.assert_called_once_with(self.path / "config.json", "w", encoding="utf-8")
        buffer.seek(0)
        for expected in self.main_file_content():
            self.assertEqual(expected, next(buffer).rstrip())

    @deprecated
    def test_save_config_key_mods(self):
        good, bad = "a", "A"
        assert any(good in k for k in Utils.CONFIG.keys()), "invalid test setup"
        assert not any(
            good in v if isinstance(v, str) else good == str(v)
            for v in Utils.CONFIG.values()
        ), "invalid test setup"
        m_open = mock.mock_open()
        buffer = StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            self.io.save_config(Utils.CONFIG, self.path, key_mods={good: bad})

        m_open.assert_called_once_with(self.path / "config.json", "w", encoding="utf-8")
        buffer.seek(0)
        for expected in self.main_file_content():
            self.assertEqual(expected.replace(good, bad), next(buffer).rstrip())
