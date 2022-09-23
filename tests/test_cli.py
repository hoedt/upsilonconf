import copy
import os
import argparse
from pathlib import Path
from unittest import TestCase
from unittest import mock

from upsilonconf.config import Configuration
from upsilonconf.cli import *

from .test_io import CONFIG, CONFIG_JSON_LINES


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
