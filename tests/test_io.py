import copy
import io
import os
import argparse
from pathlib import Path
from unittest import TestCase
from unittest import mock

from upsilonconf.config import Configuration
from upsilonconf.io import *
from upsilonconf.io import DEFAULT_NAME


CONFIG = Configuration(foo=1, bar="baz", baz={"a": 0.1, "b": 0.2})
CONFIG_JSON_LINES = (
    "{",
    '  "foo": 1,',
    '  "bar": "baz",',
    '  "baz": {',
    '    "a": 0.1,',
    '    "b": 0.2',
    "  }",
    "}",
)
CONFIG_YAML_LINES = (
    "foo: 1",
    "bar: baz",
    "baz:",
    "  a: 0.1",
    "  b: 0.2",
)


class TestFileOperations(TestCase):
    def test_save_json(self):
        path = Path.home() / "hparam.json"

        m_open = mock.mock_open()
        buffer = io.StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch("upsilonconf.io.open", m_open):
            save(CONFIG, path)

        m_open.assert_called_once_with(path, "w")
        buffer.seek(0)
        for expected, truth in zip(CONFIG_JSON_LINES, buffer):
            self.assertEqual(expected, truth.rstrip())

    def test_load_json(self):
        path = Path.home() / "hparam.json"

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_JSON_LINES))
        with mock.patch("upsilonconf.io.open", m_open):
            c = load(path)

        self.assertEqual(CONFIG, c)

    def test_save_yaml(self):
        path = Path.home() / "hparam.yaml"

        m_open = mock.mock_open()
        buffer = io.StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch("upsilonconf.io.open", m_open):
            save(CONFIG, path)

        m_open.assert_called_once_with(path, "w")
        buffer.seek(0)
        for expected, truth in zip(CONFIG_YAML_LINES, buffer):
            self.assertEqual(expected, truth.rstrip())

    def test_load_yaml(self):
        path = Path.home() / "hparam.yaml"

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_YAML_LINES))
        with mock.patch("upsilonconf.io.open", m_open):
            c = load(path)

        self.assertEqual(CONFIG, c)

    def test_load_yaml_float(self):
        path = Path.home() / "hparam.yaml"

        for expression in ("1.3e-5", "1e5", ".5e3"):
            m_open = mock.mock_open(read_data="foo: " + expression)
            with mock.patch("upsilonconf.io.open", m_open):
                c = load_yaml(path)
                self.assertEqual(float(expression), c["foo"])

    def test_save_dir(self):
        path = Path.home()

        m_open = mock.mock_open()
        buffer = io.StringIO()
        m_open.return_value.__enter__.side_effect = [buffer]
        with mock.patch("upsilonconf.io.open", m_open):
            save(CONFIG, path)

        m_open.assert_called_once_with(path / DEFAULT_NAME, "w")
        buffer.seek(0)
        for expected, truth in zip(CONFIG_JSON_LINES, buffer):
            self.assertEqual(expected, truth.rstrip())

    def test_load_dir(self):
        path = Path.home()
        filenames = (DEFAULT_NAME, "sub1.json", "sub2.json")

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_JSON_LINES))
        with mock.patch("upsilonconf.io.open", m_open), mock.patch(
            "upsilonconf.io.Path.iterdir"
        ) as m_iterdir, mock.patch("upsilonconf.io.Path.glob") as m_glob:
            m_glob.return_value = (path / name for name in filenames)
            m_iterdir.return_value = (path / name for name in filenames)
            c = load(path)

        self.assertEqual(len(filenames), m_open.call_count)
        for name in filenames[::-1]:
            m_open.assert_any_call(path / name, "r")

        self.assertDictEqual(dict(CONFIG) | {"sub1": CONFIG, "sub2": CONFIG}, dict(c))

    def test_load_dir_yaml(self):
        path = Path.home()
        filenames = ("config.yaml", "sub1.yaml", "sub2.yaml")

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_YAML_LINES))
        with mock.patch("upsilonconf.io.open", m_open), mock.patch(
            "upsilonconf.io.Path.iterdir"
        ) as m_iterdir, mock.patch("upsilonconf.io.Path.glob") as m_glob:
            m_glob.return_value = (path / name for name in filenames)
            m_iterdir.return_value = (path / name for name in filenames)
            c = load(path)

        self.assertEqual(len(filenames), m_open.call_count)
        for name in filenames[::-1]:
            m_open.assert_any_call(path / name, "r")

        self.assertDictEqual(dict(CONFIG) | {"sub1": CONFIG, "sub2": CONFIG}, dict(c))

    def test_load_dir_without_base(self):
        path = Path.home()
        filenames = ("sub1.json", "sub2.json")

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_JSON_LINES))
        with mock.patch("upsilonconf.io.open", m_open), mock.patch(
            "upsilonconf.io.Path.iterdir"
        ) as m_iterdir, mock.patch("upsilonconf.io.Path.glob") as m_glob:
            m_glob.return_value = iter(())
            m_iterdir.return_value = (path / name for name in filenames)
            c = load(path)

        self.assertEqual(len(filenames), m_open.call_count)
        for name in filenames[::-1]:
            m_open.assert_any_call(path / name, "r")

        self.assertDictEqual({"sub1": CONFIG, "sub2": CONFIG}, dict(c))

    def test_load_dir_options(self):
        path = Path.home()
        filenames = ("config.yaml", "bar.yaml")

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_YAML_LINES))
        with mock.patch("upsilonconf.io.open", m_open), mock.patch(
            "upsilonconf.io.Path.iterdir"
        ) as m_iterdir, mock.patch("upsilonconf.io.Path.glob") as m_glob:
            m_glob.return_value = (path / name for name in filenames)
            m_iterdir.return_value = (path / name for name in filenames)
            c = load(path)

        self.assertEqual(len(filenames), m_open.call_count)
        for name in filenames[::-1]:
            m_open.assert_any_call(path / name, "r")

        self.assertDictEqual(dict(CONFIG) | {"bar": CONFIG["baz"]}, dict(c))

    def test_load_dir_options_invalid(self):
        path = Path.home()
        filenames = ("config.yaml", "foo.yaml")

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_YAML_LINES))
        with mock.patch("upsilonconf.io.open", m_open), mock.patch(
            "upsilonconf.io.Path.iterdir"
        ) as m_iterdir, mock.patch("upsilonconf.io.Path.glob") as m_glob:
            m_glob.return_value = (path / name for name in filenames)
            m_iterdir.return_value = (path / name for name in filenames)
            with self.assertRaisesRegex(ValueError, filenames[-1]):
                c = load(path)

        self.assertEqual(len(filenames), m_open.call_count)
        for name in filenames[::-1]:
            m_open.assert_any_call(path / name, "r")

    def test_save_bad_extension(self):
        path = Path.home() / "hparam.invalid"
        with self.assertRaisesRegex(ValueError, "extension"):
            save(CONFIG, path)

    def test_load_bad_extension(self):
        path = Path.home() / "hparam.invalid"
        with self.assertRaisesRegex(ValueError, "extension"):
            load(path)


class TestCLI(TestCase):
    def _as_dot_keys(self, config: Configuration):
        for k, v in config.items():
            if isinstance(v, Configuration):
                yield from ((".".join([k, lk]), lv) for lk, lv in self._as_dot_keys(v))
            else:
                yield k, v

    def test_from_cli(self):
        conf = from_cli(["=".join([k, str(v)]) for k, v in self._as_dot_keys(CONFIG)])
        self.assertDictEqual(dict(CONFIG), dict(conf))

    def test_from_cli_empty(self):
        conf = from_cli([])
        self.assertDictEqual({}, dict(conf))

    def test_from_cli_config_file(self):
        path = Path.home() / "hparam.json"

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_JSON_LINES))
        with mock.patch("upsilonconf.io.open", m_open):
            c = from_cli(["--config", str(path)])

        m_open.assert_called_once_with(path, "r")
        self.assertDictEqual(dict(CONFIG), dict(c))

    def test_from_cli_override(self):
        path = Path.home() / "hparam.json"
        _k, _ = next(self._as_dot_keys(CONFIG))
        v = "new_value"
        expected = copy.deepcopy(CONFIG)
        expected.overwrite(_k, v)

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_JSON_LINES))
        with mock.patch("upsilonconf.io.open", m_open):
            c = from_cli(["--config", str(path), "=".join([_k, v])])

        self.assertDictEqual(dict(expected), dict(c))

    def test_from_cli_override_twice(self):
        path = Path.home() / "hparam.json"
        _k, _ = next(self._as_dot_keys(CONFIG))
        v = "new_value"
        expected = copy.deepcopy(CONFIG)
        expected.overwrite(_k, v)

        m_open = mock.mock_open(read_data=os.linesep.join(CONFIG_JSON_LINES))
        with mock.patch("upsilonconf.io.open", m_open):
            c = from_cli(
                ["--config", str(path), "=".join([_k, v[::-1]]), "=".join([_k, v])]
            )

        self.assertDictEqual(dict(expected), dict(c))

    def test_from_cli_parser(self):
        conf, ns = from_cli(
            ["=".join([k, str(v)]) for k, v in self._as_dot_keys(CONFIG)],
            parser=argparse.ArgumentParser(),
        )
        self.assertEqual(argparse.Namespace(), ns)
        self.assertDictEqual(dict(CONFIG), dict(conf))

    def test_from_cli_parser_options(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("positional", type=int)
        parser.add_argument("--flag", action="store_true")

        conf, ns = from_cli(["5", "--flag"], parser=parser)
        self.assertEqual(argparse.Namespace(positional=5, flag=True), ns)
        self.assertDictEqual({}, dict(conf))

    def test_from_cli_parser_options_overrides(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("positional", type=int)
        parser.add_argument("--flag", action="store_true")

        k, v = "key", "value"
        conf, ns = from_cli(["--flag", "5", "=".join([k, v])], parser=parser)
        self.assertEqual(argparse.Namespace(positional=5, flag=True), ns)
        self.assertDictEqual({k: v}, dict(conf))
