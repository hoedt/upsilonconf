import os
from io import StringIO
from typing import Iterable
from unittest import TestCase, mock

from upsilonconf.io.base import *
from upsilonconf.io.json import JSONIO
from upsilonconf.io.yaml import YAMLIO
from upsilonconf.config import ConfigurationBase, PlainConfiguration


class Utils:
    CONFIG = PlainConfiguration(foo=1, bar="test", baz={"a": 0.1, "b": 0.2})
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
            cls.file_path = Path.home() / "config.json"
            cls.file_contents = "\n".join(cls.generate_file_content())

        def setUp(self) -> None:
            self.io = self.default_io()

        def test_read_from(self):
            buffer = StringIO(self.file_contents)
            data = self.io.read_from(buffer)
            self.assertDictEqual(Utils.CONFIG.to_dict(), dict(data))

        def test_read_from_whitespace_key(self):
            buffer = StringIO(self.file_contents.replace("foo", "space foo"))
            data = self.io.read_from(buffer)
            ref = Utils.CONFIG.to_dict(key_mods={"foo": "space foo"})
            self.assertDictEqual(ref, dict(data))

        def test_read(self):
            m_open = mock.mock_open(read_data=self.file_contents)
            with mock.patch("upsilonconf.io.base.open", m_open):
                data = self.io.read(self.file_path)

            m_open.assert_called_once_with(self.file_path, "r", encoding="utf-8")
            self.assertDictEqual(Utils.CONFIG.to_dict(), dict(data))

        def test_read_encoding(self):
            m_open = mock.mock_open(read_data=self.file_contents)
            with mock.patch("upsilonconf.io.base.open", m_open):
                data = self.io.read(self.file_path, encoding="ascii")

            m_open.assert_called_once_with(self.file_path, "r", encoding="ascii")
            self.assertDictEqual(Utils.CONFIG.to_dict(), dict(data))

        def test_write_to(self):
            buffer = StringIO()
            self.io.write_to(buffer, Utils.CONFIG.to_dict())
            buffer.seek(0)
            self.assertMultiLineEqual(self.file_contents, buffer.getvalue().rstrip())

        def test_write_to_whitespace_key(self):
            buffer = StringIO()
            d = Utils.CONFIG.to_dict(key_mods={"foo": "space foo"})
            self.io.write_to(buffer, d)
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
                self.io.write(Utils.CONFIG.to_dict(), self.file_path)

            m_open.assert_called_once_with(self.file_path, "w", encoding="utf-8")
            buffer.seek(0)
            for expected in self.generate_file_content():
                self.assertEqual(expected, next(buffer).rstrip())

        def test_write_encoding(self):
            m_open = mock.mock_open()
            buffer = StringIO()
            m_open.return_value.__enter__.side_effect = [buffer]
            with mock.patch("upsilonconf.io.base.open", m_open):
                self.io.write(Utils.CONFIG.to_dict(), self.file_path, encoding="ascii")

            m_open.assert_called_once_with(self.file_path, "w", encoding="ascii")
            buffer.seek(0)
            for expected in self.generate_file_content():
                self.assertEqual(expected, next(buffer).rstrip())

        def test_load_config(self):
            m_open = mock.mock_open(read_data=self.file_contents)
            with mock.patch("upsilonconf.io.base.open", m_open):
                config = self.io.load_config(self.file_path)

            m_open.assert_called_once_with(self.file_path, "r", encoding="utf-8")
            self.assertIsInstance(config, ConfigurationBase)
            self.assertEqual(Utils.CONFIG, config)

        def test_load_config_relative_path(self):
            filename = self.file_path.name
            m_open = mock.mock_open(read_data=self.file_contents)
            with mock.patch("upsilonconf.io.base.open", m_open):
                config = self.io.load_config(filename)

            m_open.assert_called_once_with(Path.cwd() / filename, "r", encoding="utf-8")
            self.assertIsInstance(config, ConfigurationBase)
            self.assertEqual(Utils.CONFIG, config)

        def test_load_config_user_path(self):
            filename = self.file_path.name
            m_open = mock.mock_open(read_data=self.file_contents)
            with mock.patch("upsilonconf.io.base.open", m_open):
                config = self.io.load_config(Path("~") / filename)

            m_open.assert_called_once_with(
                Path.home() / filename, "r", encoding="utf-8"
            )
            self.assertIsInstance(config, ConfigurationBase)
            self.assertEqual(Utils.CONFIG, config)

        def test_load_config_whitespace_key(self):
            file_contents = self.file_contents.replace("foo", "space foo")
            m_open = mock.mock_open(read_data=file_contents)
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

            m_open.assert_called_once_with(self.file_path, "r", encoding="utf-8")
            self.assertIsInstance(config, ConfigurationBase)
            self.assertEqual(Utils.CONFIG, config)

        def test_save_config(self):
            m_open = mock.mock_open()
            buffer = StringIO()
            m_open.return_value.__enter__.side_effect = [buffer]
            with mock.patch("upsilonconf.io.base.open", m_open):
                self.io.save_config(Utils.CONFIG, self.file_path)

            m_open.assert_called_once_with(self.file_path, "w", encoding="utf-8")
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

            m_open.assert_called_once_with(Path.cwd() / filename, "w", encoding="utf-8")
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

            m_open.assert_called_once_with(
                Path.home() / filename, "w", encoding="utf-8"
            )
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

            m_open.assert_called_once_with(self.file_path, "w", encoding="utf-8")
            buffer.seek(0)
            for expected in self.generate_file_content():
                self.assertEqual(expected.replace(good, bad), next(buffer).rstrip())


class TestExtensionIO(Utils.TestConfigIO):
    @staticmethod
    def generate_file_content():
        yield from Utils.DEFAULT_LINES

    @staticmethod
    def default_io():
        return ExtensionIO(JSONIO(), YAMLIO())

    @staticmethod
    def generate_other_content():
        yield "foo: 1"
        yield "bar: test"
        yield "baz:"
        yield "  a: 0.1"
        yield "  b: 0.2"

    def test_constructor(self):
        json_io, yaml_io = JSONIO(), YAMLIO()
        io = ExtensionIO(json_io, yaml_io)
        self.assertEqual(".json", io.default_ext)
        self.assertIn(".json", io.extensions)
        self.assertIn(".yaml", io.extensions)
        self.assertIn(".yml", io.extensions)

    def test_constructor_default_ext(self):
        json_io, yaml_io = JSONIO(), YAMLIO()
        io = ExtensionIO(json_io, yaml_io, default_ext=".yml")
        self.assertEqual(".yml", io.default_ext)
        self.assertIn(".json", io.extensions)
        self.assertIn(".yaml", io.extensions)
        self.assertIn(".yml", io.extensions)

    def test_constructor_empty(self):
        with self.assertRaises(TypeError):
            ExtensionIO()

    def test_constructor_default_ext_without_period(self):
        io = ExtensionIO(JSONIO(), default_ext="json")
        self.assertEqual(".json", io.default_ext)

    def test_constructor_default_ext_not_registered(self):
        with self.assertRaisesRegex(ValueError, "not supported"):
            ExtensionIO(JSONIO(), default_ext=".yaml")

    def test_getitem(self):
        self.assertIsInstance(self.io[".json"], JSONIO)
        self.assertIsInstance(self.io[".yaml"], YAMLIO)

    def test_getitem_capitalised(self):
        self.assertIsInstance(self.io[".JSON"], JSONIO)
        self.assertIsInstance(self.io[".YAML"], YAMLIO)

    def test_getitem_no_dot(self):
        self.assertIsInstance(self.io["json"], JSONIO)
        self.assertIsInstance(self.io["yaml"], YAMLIO)

    def test_getitem_bad_key(self):
        with self.assertRaisesRegex(KeyError, ".invalid"):
            _ = self.io[".invalid"]

    def test_setitem(self):
        new_io = JSONIO()
        self.io[".jason"] = new_io
        self.assertIn(".jason", self.io.extensions)
        self.assertIs(new_io, self.io[".jason"])

    def test_setitem_capitalised(self):
        new_io = JSONIO()
        self.io[".JASON"] = new_io
        self.assertIn(".jason", self.io.extensions)
        self.assertIs(new_io, self.io[".jason"])

    def test_setitem_no_dot(self):
        new_io = JSONIO()
        self.io["jason"] = new_io
        self.assertIn(".jason", self.io.extensions)
        self.assertIs(new_io, self.io[".jason"])

    def test_setitem_overwrite(self):
        new_io = JSONIO()
        self.io[".json"] = new_io
        self.assertIs(new_io, self.io[".json"])

    def test_delitem(self):
        expected_length = len(self.io.extensions) - 1
        del self.io[".yaml"]
        self.assertEqual(expected_length, len(self.io.extensions))
        self.assertNotIn(".yaml", self.io.extensions)
        self.assertIn(".json", self.io.extensions)
        self.assertIn(".yml", self.io.extensions)

    def test_delitem_capitalised(self):
        expected_length = len(self.io.extensions) - 1
        del self.io[".YAML"]
        self.assertEqual(expected_length, len(self.io.extensions))
        self.assertNotIn(".yaml", self.io.extensions)
        self.assertIn(".json", self.io.extensions)
        self.assertIn(".yml", self.io.extensions)

    def test_delitem_no_dot(self):
        expected_length = len(self.io.extensions) - 1
        del self.io["yaml"]
        self.assertEqual(expected_length, len(self.io.extensions))
        self.assertNotIn(".yaml", self.io.extensions)
        self.assertIn(".json", self.io.extensions)
        self.assertIn(".yml", self.io.extensions)

    def test_delitem_bad_key(self):
        with self.assertRaisesRegex(KeyError, ".invalid"):
            del self.io[".invalid"]

    def test_delitem_default(self):
        default_ext = self.io.default_ext
        expected_length = len(self.io.extensions)
        with self.assertRaises(ValueError):
            del self.io[default_ext]
        self.assertEqual(expected_length, len(self.io.extensions))

    def test_delitem_all(self):
        with self.assertRaises(ValueError):
            for ext in self.io.extensions:
                del self.io[ext]
        self.assertGreaterEqual(len(self.io.extensions), 1)

    def test_length(self):
        io1 = ExtensionIO(JSONIO())
        self.assertEqual(1, len(io1))
        io2 = ExtensionIO(YAMLIO())
        self.assertEqual(2, len(io2))
        io3 = ExtensionIO(JSONIO(), YAMLIO())
        self.assertEqual(3, len(io3))

    def test_iter(self):
        for ext in iter(self.io):
            self.assertIsNotNone(self.io[ext])

    def test_default_ext_setter(self):
        for ext in self.io.extensions:
            self.io.default_ext = ext
            self.assertEqual(ext, self.io.default_ext)

    def test_default_ext_capitalised(self):
        for ext in self.io.extensions:
            self.io.default_ext = ext.upper()
            self.assertEqual(ext, self.io.default_ext)

    def test_default_ext_no_dot(self):
        for ext in self.io.extensions:
            self.io.default_ext = ext.lstrip(".")
            self.assertEqual(ext, self.io.default_ext)

    def test_default_ext_bad_ext(self):
        with self.assertRaises(ValueError):
            self.io.default_ext = ".invalid"

    def test_read_from(self):
        buffer = StringIO(self.file_contents)
        with self.assertRaises(TypeError):
            self.io.read_from(buffer)

    def test_read_from_whitespace_key(self):
        buffer = StringIO(self.file_contents)
        with self.assertRaises(TypeError):
            self.io.read_from(buffer)

    def test_read_unknown_ext(self):
        with self.assertRaisesRegex(ValueError, "extension"):
            self.io.read(self.file_path.with_suffix(".invalid"))

    def test_write_to(self):
        buffer = StringIO()
        with self.assertRaises(TypeError):
            self.io.write_to(buffer, Utils.CONFIG.to_dict())

    def test_write_to_whitespace_key(self):
        buffer = StringIO()
        with self.assertRaises(TypeError):
            self.io.write_to(buffer, Utils.CONFIG.to_dict())

    def test_write_to_config(self):
        buffer = StringIO()
        with self.assertRaises(TypeError):
            self.io.write_to(buffer, Utils.CONFIG)

    def test_write_unknown_ext(self):
        with self.assertRaisesRegex(ValueError, "extension"):
            self.io.write(Utils.CONFIG, self.file_path.with_suffix(".invalid"))

    def test_load_config_unknown_ext(self):
        with self.assertRaisesRegex(ValueError, "extension"):
            self.io.load_config(self.file_path.with_suffix(".invalid"))

    def test_save_config_unknown_ext(self):
        with self.assertRaisesRegex(ValueError, "extension"):
            self.io.save_config(Utils.CONFIG, self.file_path.with_suffix(".invalid"))

    def test_read_non_default_ext(self):
        file_contents = os.linesep.join(self.generate_other_content())
        m_open = mock.mock_open(read_data=file_contents)
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            data = self.io.read(self.file_path.with_suffix(".yml"))

        m_open.assert_called_once_with(
            self.file_path.with_suffix(".yml"), "r", encoding="utf-8"
        )
        self.assertDictEqual(dict(Utils.CONFIG), dict(data))

    def test_write_non_default_ext(self):
        file_path = self.file_path.with_suffix(".yml")
        m_open = mock.mock_open()
        buffer = StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            self.io.write(dict(Utils.CONFIG), file_path)

        m_open.assert_called_once_with(file_path, "w", encoding="utf-8")
        buffer.seek(0)
        for expected in self.generate_other_content():
            self.assertEqual(expected, next(buffer).rstrip())

    def test_load_config_non_default_ext(self):
        file_contents = os.linesep.join(self.generate_other_content())
        m_open = mock.mock_open(read_data=file_contents)
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            config = self.io.load_config(self.file_path.with_suffix(".yml"))

        m_open.assert_called_once_with(
            self.file_path.with_suffix(".yml"), "r", encoding="utf-8"
        )
        self.assertIsInstance(config, ConfigurationBase)
        self.assertEqual(Utils.CONFIG, config)

    def test_save_config_non_default_ext(self):
        file_path = self.file_path.with_suffix(".yml")
        m_open = mock.mock_open()
        buffer = StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch(f"upsilonconf.io.base.open", m_open):
            self.io.save_config(Utils.CONFIG, file_path)

        m_open.assert_called_once_with(file_path, "w", encoding="utf-8")
        buffer.seek(0)
        for expected in self.generate_other_content():
            self.assertEqual(expected, next(buffer).rstrip())
