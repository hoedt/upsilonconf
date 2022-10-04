import os
from io import StringIO
from typing import Iterable
from unittest import TestCase, mock

from upsilonconf.base import InvalidKeyError
from upsilonconf.io.base import *
from upsilonconf.io.json import JSONIO
from upsilonconf.io.yaml import YAMLIO


class Utils:

    CONFIG = Configuration(foo=1, bar="test", baz={"a": 0.1, "b": 0.2})
    DEFAULT_LINES = (
        "{",
        '  "foo": 1,',
        '  "bar": "test",',
        '  "baz": {',
        '    "a": 0.1,',
        '    "b": 0.2',
        "  }",
        "}",
    )

    class TestConfigIO(TestCase):
        @staticmethod
        def generate_file_content() -> Iterable[str]:
            raise NotImplementedError()

        @staticmethod
        def default_io():
            raise NotImplementedError()

        @classmethod
        def setUpClass(cls):
            cls.file_path = Path.home() / "config.test"
            cls.file_contents = "\n".join(cls.generate_file_content())

        def setUp(self) -> None:
            self.io = self.default_io()

        def test_default_ext(self):
            self.assertEqual(self.io.default_ext, self.io.extensions[0])

        def test_read_from(self):
            buffer = StringIO(self.file_contents)
            data = self.io.read_from(buffer)
            self.assertDictEqual(dict(Utils.CONFIG), dict(data))

        def test_read_from_whitespace_key(self):
            buffer = StringIO(self.file_contents.replace("foo", "space foo"))
            data = self.io.read_from(buffer)
            ref = {
                ("space " + k if k == "foo" else k): v for k, v in Utils.CONFIG.items()
            }
            self.assertDictEqual(ref, dict(data))

        def test_read(self):
            m_open = mock.mock_open(read_data=self.file_contents)
            with mock.patch("upsilonconf.io.base.open", m_open):
                data = self.io.read(self.file_path)

            m_open.assert_called_once_with(self.file_path, "r")
            self.assertDictEqual(dict(Utils.CONFIG), dict(data))

        def test_write_to(self):
            buffer = StringIO()
            self.io.write_to(buffer, dict(Utils.CONFIG))
            buffer.seek(0)
            self.assertMultiLineEqual(self.file_contents, buffer.getvalue().rstrip())

        def test_write_to_whitespace_key(self):
            buffer = StringIO()
            self.io.write_to(
                buffer,
                {
                    ("space " + k if k == "foo" else k): v
                    for k, v in Utils.CONFIG.items()
                },
            )
            buffer.seek(0)
            ref = self.file_contents.replace("foo", "space foo")
            self.assertMultiLineEqual(ref, buffer.getvalue().rstrip())

        def test_write_to_config(self):
            buffer = StringIO()
            self.io.write_to(buffer, Utils.CONFIG)
            buffer.seek(0)
            self.assertMultiLineEqual(self.file_contents, buffer.getvalue().rstrip())

        def test_write(self):
            m_open = mock.mock_open()
            buffer = StringIO()
            m_open.return_value.__enter__.side_effect = [buffer]
            with mock.patch("upsilonconf.io.base.open", m_open):
                self.io.write(dict(Utils.CONFIG), self.file_path)

            m_open.assert_called_once_with(self.file_path, "w")
            buffer.seek(0)
            for expected in self.generate_file_content():
                self.assertEqual(expected, next(buffer).rstrip())

        def test_load_config(self):
            m_open = mock.mock_open(read_data=self.file_contents)
            with mock.patch("upsilonconf.io.base.open", m_open):
                config = self.io.load_config(self.file_path)

            m_open.assert_called_once_with(self.file_path, "r")
            self.assertIsInstance(config, Configuration)
            self.assertEqual(Utils.CONFIG, config)

        def test_load_config_relative_path(self):
            filename = self.file_path.name
            m_open = mock.mock_open(read_data=self.file_contents)
            with mock.patch("upsilonconf.io.base.open", m_open):
                config = self.io.load_config(filename)

            m_open.assert_called_once_with(Path.cwd() / filename, "r")
            self.assertIsInstance(config, Configuration)
            self.assertEqual(Utils.CONFIG, config)

        def test_load_config_user_path(self):
            filename = self.file_path.name
            m_open = mock.mock_open(read_data=self.file_contents)
            with mock.patch("upsilonconf.io.base.open", m_open):
                config = self.io.load_config(Path("~") / filename)

            m_open.assert_called_once_with(Path.home() / filename, "r")
            self.assertIsInstance(config, Configuration)
            self.assertEqual(Utils.CONFIG, config)

        def test_load_config_whitespace_key(self):
            file_contents = self.file_contents.replace("foo", "space foo")
            m_open = mock.mock_open(read_data=file_contents)
            with self.assertRaises(InvalidKeyError):
                with mock.patch("upsilonconf.io.base.open", m_open):
                    self.io.load_config(self.file_path)

        def test_load_config_key_mods(self):
            good, bad = "a", "A"
            assert any(good in k for k in Utils.CONFIG.keys()), "invalid test setup"
            assert not any(
                good in v if isinstance(v, str) else good == str(v)
                for v in Utils.CONFIG.values()
            ), "invalid test setup"
            m_open = mock.mock_open(read_data=self.file_contents.replace(good, bad))
            with mock.patch("upsilonconf.io.base.open", m_open):
                config = self.io.load_config(self.file_path, key_mods={bad: good})

            m_open.assert_called_once_with(self.file_path, "r")
            self.assertIsInstance(config, Configuration)
            self.assertEqual(Utils.CONFIG, config)

        def test_save_config(self):
            m_open = mock.mock_open()
            buffer = StringIO()
            m_open.return_value.__enter__.side_effect = [buffer]
            with mock.patch("upsilonconf.io.base.open", m_open):
                self.io.save_config(Utils.CONFIG, self.file_path)

            m_open.assert_called_once_with(self.file_path, "w")
            buffer.seek(0)
            for expected in self.generate_file_content():
                self.assertEqual(expected, next(buffer).rstrip())

        def test_save_config_relative_path(self):
            filename = self.file_path.name
            m_open = mock.mock_open()
            buffer = StringIO()
            m_open.return_value.__enter__.side_effect = [buffer]
            with mock.patch("upsilonconf.io.base.open", m_open):
                self.io.save_config(Utils.CONFIG, filename)

            m_open.assert_called_once_with(Path.cwd() / filename, "w")
            buffer.seek(0)
            for expected in self.generate_file_content():
                self.assertEqual(expected, next(buffer).rstrip())

        def test_save_config_user_path(self):
            filename = self.file_path.name
            m_open = mock.mock_open()
            buffer = StringIO()
            m_open.return_value.__enter__.side_effect = [buffer]
            with mock.patch("upsilonconf.io.base.open", m_open):
                self.io.save_config(Utils.CONFIG, Path("~") / filename)

            m_open.assert_called_once_with(Path.home() / filename, "w")
            buffer.seek(0)
            for expected in self.generate_file_content():
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
            with mock.patch("upsilonconf.io.base.open", m_open):
                self.io.save_config(Utils.CONFIG, self.file_path, key_mods={good: bad})

            m_open.assert_called_once_with(self.file_path, "w")
            buffer.seek(0)
            for expected in self.generate_file_content():
                self.assertEqual(expected.replace(good, bad), next(buffer).rstrip())


class TestFlexibleIO(Utils.TestConfigIO):
    @staticmethod
    def generate_file_content():
        yield from Utils.DEFAULT_LINES

    @staticmethod
    def default_io():
        return FlexibleIO(
            {
                ".test": JSONIO(),
                ".other": YAMLIO(),
            }
        )

    @staticmethod
    def generate_other_content():
        yield "foo: 1"
        yield "bar: test"
        yield "baz:"
        yield "  a: 0.1"
        yield "  b: 0.2"

    def test_constructor(self):
        default_io = JSONIO()
        io = FlexibleIO({".json": default_io, ".jason": JSONIO()})
        self.assertIs(default_io, io.default_io)
        self.assertIn(".json", io.extensions)
        self.assertIn(".jason", io.extensions)

    def test_constructor_default_ext(self):
        default_io = JSONIO()
        io = FlexibleIO({".json": JSONIO(), ".jason": default_io}, default_ext=".jason")
        self.assertIs(default_io, io.default_io)
        self.assertIn(".json", io.extensions)
        self.assertIn(".jason", io.extensions)

    def test_constructor_empty(self):
        with self.assertRaises(ValueError):
            FlexibleIO({})

    def test_constructor_ext_without_period(self):
        with self.assertRaisesRegex(ValueError, "extension .* period"):
            FlexibleIO({"json": JSONIO()})

    def test_constructor_default_ext_without_period(self):
        with self.assertRaisesRegex(ValueError, "no IO"):
            FlexibleIO({".json": JSONIO()}, default_ext="json")

    def test_constructor_default_ext_not_registered(self):
        with self.assertRaisesRegex(ValueError, "no IO"):
            FlexibleIO({".json": JSONIO()}, default_ext=".yaml")

    def test_update(self):
        self.io.update(".added", self.io)
        self.assertIn(".added", self.io._ext_io_map)
        self.assertIs(self.io._ext_io_map[".added"], self.io)

    def test_update_overwrite(self):
        new_io = JSONIO()
        self.io.update(".other", new_io)
        self.assertIs(self.io._ext_io_map[".other"], new_io)

    def test_update_bad_ext(self):
        with self.assertRaisesRegex(ValueError, "extension"):
            self.io.update("added", JSONIO())

    def test_read_unknown_ext(self):
        with self.assertRaisesRegex(ValueError, "extension"):
            self.io.read(self.file_path.with_suffix(".invalid"))

    def test_write_unknown_ext(self):
        with self.assertRaisesRegex(ValueError, "extension"):
            self.io.write(Utils.CONFIG, self.file_path.with_suffix(".invalid"))

    def test_load_config_unknown_ext(self):
        with self.assertRaisesRegex(ValueError, "extension"):
            self.io.load_config(self.file_path.with_suffix(".invalid"))

    def test_save_config_unknown_ext(self):
        with self.assertRaisesRegex(ValueError, "extension"):
            self.io.save_config(Utils.CONFIG, self.file_path.with_suffix(".invalid"))

    def test_read_other_ext(self):
        file_contents = os.linesep.join(self.generate_other_content())
        m_open = mock.mock_open(read_data=file_contents)
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            data = self.io.read(self.file_path.with_suffix(".other"))

        m_open.assert_called_once_with(self.file_path.with_suffix(".other"), "r")
        self.assertDictEqual(dict(Utils.CONFIG), dict(data))

    def test_write_other_ext(self):
        file_path = self.file_path.with_suffix(".other")
        m_open = mock.mock_open()
        buffer = StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            self.io.write(dict(Utils.CONFIG), file_path)

        m_open.assert_called_once_with(file_path, "w")
        buffer.seek(0)
        for expected in self.generate_other_content():
            self.assertEqual(expected, next(buffer).rstrip())

    def test_load_config_other_ext(self):
        file_contents = os.linesep.join(self.generate_other_content())
        m_open = mock.mock_open(read_data=file_contents)
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            config = self.io.load_config(self.file_path.with_suffix(".other"))

        m_open.assert_called_once_with(self.file_path.with_suffix(".other"), "r")
        self.assertIsInstance(config, Configuration)
        self.assertEqual(Utils.CONFIG, config)

    def test_save_config_other_ext(self):
        file_path = self.file_path.with_suffix(".other")
        m_open = mock.mock_open()
        buffer = StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            self.io.save_config(Utils.CONFIG, file_path)

        m_open.assert_called_once_with(file_path, "w")
        buffer.seek(0)
        for expected in self.generate_other_content():
            self.assertEqual(expected, next(buffer).rstrip())
