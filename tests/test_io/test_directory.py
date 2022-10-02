import os
from io import StringIO
from pathlib import Path
from unittest import TestCase, mock

from upsilonconf.io.directory import *
from upsilonconf.io.json import JSONIO
from upsilonconf.io.yaml import YAMLIO
from upsilonconf.io.base import FlexibleIO
from .test_base import Utils


def fake_directory_structure(root, paths):
    root = Path(root)

    class _MockedScandirIterator:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def __iter__(self):
            yield from (Configuration(name=sub) for sub in paths)

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

    def test_read_from(self):
        with self.assertRaises(TypeError):
            self.io.read_from(StringIO())

    @fake_directory_structure(path, ["config.json"])
    def test_read(self):
        m_open = mock.mock_open(read_data=self.file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            data = self.io.read(self.path)

        m_open.assert_called_once_with(self.path / "config.json", "r")
        self.assertDictEqual(dict(Utils.CONFIG), dict(data))

    @fake_directory_structure(path, ["config.yaml"])
    def test_read_non_default(self):
        io = DirectoryIO(FlexibleIO({".json": JSONIO(), ".yaml": YAMLIO()}))
        assert io.default_ext == ".json", "invalid test setup"

        m_open = mock.mock_open(read_data=self.file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            data = io.read(self.path)

        m_open.assert_called_once_with(self.path / "config.yaml", "r")
        self.assertDictEqual(dict(Utils.CONFIG), dict(data))

    @fake_directory_structure(path, ["config.json", "sub1.json", "sub2.json"])
    def test_read_multiple(self):
        m_open = mock.mock_open(read_data=self.file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            data = self.io.read(self.path)

        m_open.assert_has_calls(
            [
                mock.call(self.path / "config.json", "r"),
                mock.call(self.path / "sub1.json", "r"),
                mock.call(self.path / "sub2.json", "r"),
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
                mock.call(self.path / "sub1.json", "r"),
                mock.call(self.path / "sub2.json", "r"),
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
                mock.call(self.path / "config.json", "r"),
                mock.call(self.path / "foo.json", "r"),
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

    @fake_directory_structure(path, ["config.json", "sub1.json", "sub2.json"])
    def test_load_config(self):
        m_open = mock.mock_open(read_data=self.file_contents)
        with mock.patch("upsilonconf.io.base.open", m_open):
            config = self.io.load_config(self.path)

        m_open.assert_has_calls(
            [
                mock.call(self.path / "config.json", "r"),
                mock.call(self.path / "sub1.json", "r"),
                mock.call(self.path / "sub2.json", "r"),
            ],
            any_order=True,
        )
        self.assertEqual(3, m_open.call_count)
        self.assertIsInstance(config, Configuration)
        ref = Configuration(**Utils.CONFIG, sub1=Utils.CONFIG, sub2=Utils.CONFIG)
        self.assertEqual(ref, config)

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
                mock.call(self.path / "config.json", "r"),
                mock.call(self.path / "sub1.json", "r"),
                mock.call(self.path / "sub2.json", "r"),
            ],
            any_order=True,
        )
        self.assertEqual(3, m_open.call_count)
        self.assertIsInstance(config, Configuration)
        ref = Configuration(**Utils.CONFIG, sub1=Utils.CONFIG, sub2=Utils.CONFIG)
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

        m_open.assert_called_once_with(self.path / "config.json", "w")
        buffer.seek(0)
        for expected in self.main_file_content():
            self.assertEqual(expected, next(buffer).rstrip())

    def test_write_config(self):
        m_open = mock.mock_open()
        buffer = StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            self.io.write(Utils.CONFIG, self.path)

        m_open.assert_called_once_with(self.path / "config.json", "w")
        buffer.seek(0)
        for expected in self.main_file_content():
            self.assertEqual(expected, next(buffer).rstrip())

    def test_save_config(self):
        m_open = mock.mock_open()
        buffer = StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            self.io.save_config(Utils.CONFIG, self.path)

        m_open.assert_called_once_with(self.path / "config.json", "w")
        buffer.seek(0)
        for expected in self.main_file_content():
            self.assertEqual(expected, next(buffer).rstrip())

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

        m_open.assert_called_once_with(self.path / "config.json", "w")
        buffer.seek(0)
        for expected in self.main_file_content():
            self.assertEqual(expected.replace(good, bad), next(buffer).rstrip())

    # TODO: hierarchy tests!!!
