import os
from argparse import ArgumentParser, Namespace
from pathlib import Path
from unittest import TestCase, mock

from .test_base import Utils, deprecated
from upsilonconf.io.cli import *
from upsilonconf.io import JSONIO
from upsilonconf.config import ConfigurationBase, CarefulConfiguration


def _as_dot_keys(config: ConfigurationBase):
    """Utility for converting config to dot-lists"""
    for k, v in config.items():
        if isinstance(v, ConfigurationBase):
            yield from ((".".join([k, lk]), lv) for lk, lv in _as_dot_keys(v))
        else:
            yield k, v


class TestConfigParser(TestCase):
    def setUp(self):
        self.cli = ConfigParser(JSONIO())

    def test_constructor_minimal(self):
        cli = ConfigParser(JSONIO())
        self.assertFalse(cli.return_ns)
        self.assertIsNotNone(cli.parser)
        self.assertIn("KEY=VALUE", cli.parser.format_usage())
        self.assertIn("--config", cli.parser.format_usage())

    def test_constructor_parser(self):
        parser = ArgumentParser()
        cli = ConfigParser(JSONIO(), parser=parser)
        self.assertTrue(cli.return_ns)
        self.assertEqual(parser, cli.parser)
        self.assertIn("KEY=VALUE", cli.parser.format_usage())
        self.assertIn("--config", cli.parser.format_usage())

    def test_constructor_io(self):
        cli = ConfigParser(JSONIO())
        self.assertFalse(cli.return_ns)
        self.assertIsNotNone(cli.parser)
        self.assertIn("KEY=VALUE", cli.parser.format_usage())
        self.assertIn("--config", cli.parser.format_usage())

    def test_constructor_combination(self):
        parser = ArgumentParser()
        cli = ConfigParser(JSONIO(), parser=parser, return_ns=False)
        self.assertFalse(cli.return_ns)
        self.assertEqual(parser, cli.parser)
        self.assertIn("KEY=VALUE", cli.parser.format_usage())
        self.assertIn("--config", cli.parser.format_usage())

    def test_parse_cli(self):
        expected = dict(_as_dot_keys(Utils.CONFIG))
        mapping = self.cli.parse_cli([f"{k}={v!s}" for k, v in expected.items()])
        self.assertDictEqual(expected, mapping)

    def test_parse_cli_empty(self):
        mapping = self.cli.parse_cli([])
        self.assertDictEqual({}, dict(mapping))

    def test_parse_cli_return_ns(self):
        self.cli.return_ns = True
        expected = dict(_as_dot_keys(Utils.CONFIG))
        mapping, ns = self.cli.parse_cli([f"{k}={v!s}" for k, v in expected.items()])
        self.assertDictEqual(expected, mapping)
        self.assertEqual(Namespace(), ns)

    def test_parse_cli_file(self):
        cli = ConfigParser(config_io=JSONIO())
        m_open = mock.mock_open(read_data=os.linesep.join(Utils.DEFAULT_LINES))
        with mock.patch("upsilonconf.io.base.open", m_open):
            config = cli.parse_cli(["--config", "hparam.json"])

        m_open.assert_called_once_with(
            Path.cwd() / "hparam.json", "r", encoding="utf-8"
        )
        self.assertDictEqual(Utils.CONFIG.to_dict(), config)

    def test_parse_cli_override(self):
        _k, _ = next(_as_dot_keys(Utils.CONFIG))
        v = "new value"

        cli = ConfigParser(config_io=JSONIO())
        m_open = mock.mock_open(read_data=os.linesep.join(Utils.DEFAULT_LINES))
        with mock.patch("upsilonconf.io.base.open", m_open):
            mapping = cli.parse_cli(["--config", "hparam.json", "=".join([_k, v])])

        m_open.assert_called_once_with(
            Path.cwd() / "hparam.json", "r", encoding="utf-8"
        )
        self.assertEqual(Utils.CONFIG.to_dict() | {_k: v}, mapping)

    def test_parse_cli_override_twice(self):
        _k, _ = next(_as_dot_keys(Utils.CONFIG))
        v = "new value"

        cli = ConfigParser(config_io=JSONIO())
        m_open = mock.mock_open(read_data=os.linesep.join(Utils.DEFAULT_LINES))
        with mock.patch("upsilonconf.io.base.open", m_open):
            mapping = cli.parse_cli(
                ["--config", "hparam.json", "=".join([_k, v[::-1]]), "=".join([_k, v])]
            )

        m_open.assert_called_once_with(
            Path.cwd() / "hparam.json", "r", encoding="utf-8"
        )
        self.assertEqual(Utils.CONFIG.to_dict() | {_k: v}, mapping)

    def test_parse_cli_parser_options(self):
        parser = ArgumentParser()
        parser.add_argument("positional", type=int)
        parser.add_argument("--flag", action="store_true")

        cli = ConfigParser(JSONIO(), parser=parser)
        mapping, ns = cli.parse_cli(["5", "--flag"])
        self.assertEqual(Namespace(positional=5, flag=True), ns)
        self.assertDictEqual({}, mapping)

    def test_parse_cli_parser_options_overrides(self):
        parser = ArgumentParser()
        parser.add_argument("positional", type=int)
        parser.add_argument("--flag", action="store_true")

        k, v = "key", "value"
        cli = ConfigParser(JSONIO(), parser=parser)
        mapping, ns = cli.parse_cli(["--flag", "5", "=".join([k, v])])
        self.assertEqual(Namespace(positional=5, flag=True), ns)
        self.assertDictEqual({k: v}, mapping)

    @deprecated
    def test_parse_config(self):
        args = [f"{k}={v!s}" for k, v in _as_dot_keys(Utils.CONFIG)]
        config = self.cli.parse_config(args)
        self.assertEqual(Utils.CONFIG, config)

    @deprecated
    def test_parse_config_empty(self):
        config = self.cli.parse_config([])
        self.assertDictEqual({}, dict(config))

    @deprecated
    def test_parse_config_return_ns(self):
        self.cli.return_ns = True
        args = [f"{k}={v!s}" for k, v in _as_dot_keys(Utils.CONFIG)]
        config, ns = self.cli.parse_config(args)
        self.assertEqual(Utils.CONFIG, config)
        self.assertEqual(Namespace(), ns)

    @deprecated
    def test_parse_config_file(self):
        cli = ConfigParser(config_io=JSONIO())
        m_open = mock.mock_open(read_data=os.linesep.join(Utils.DEFAULT_LINES))
        with mock.patch("upsilonconf.io.base.open", m_open):
            config = cli.parse_config(["--config", "hparam.json"])

        m_open.assert_called_once_with(
            Path.cwd() / "hparam.json", "r", encoding="utf-8"
        )
        self.assertEqual(Utils.CONFIG, config)

    @deprecated
    def test_parse_config_override(self):
        _k, _ = next(_as_dot_keys(Utils.CONFIG))
        v = "new value"
        expected = CarefulConfiguration(**Utils.CONFIG)
        expected.overwrite(_k, v)

        cli = ConfigParser(config_io=JSONIO())
        m_open = mock.mock_open(read_data=os.linesep.join(Utils.DEFAULT_LINES))
        with mock.patch("upsilonconf.io.base.open", m_open):
            config = cli.parse_config(["--config", "hparam.json", "=".join([_k, v])])

        m_open.assert_called_once_with(
            Path.cwd() / "hparam.json", "r", encoding="utf-8"
        )
        self.assertEqual(expected, config)

    @deprecated
    def test_parse_config_override_twice(self):
        _k, _ = next(_as_dot_keys(Utils.CONFIG))
        v = "new value"
        expected = CarefulConfiguration(**Utils.CONFIG)
        expected.overwrite(_k, v)

        cli = ConfigParser(config_io=JSONIO())
        m_open = mock.mock_open(read_data=os.linesep.join(Utils.DEFAULT_LINES))
        with mock.patch("upsilonconf.io.base.open", m_open):
            config = cli.parse_config(
                ["--config", "hparam.json", "=".join([_k, v[::-1]]), "=".join([_k, v])]
            )

        m_open.assert_called_once_with(
            Path.cwd() / "hparam.json", "r", encoding="utf-8"
        )
        self.assertEqual(expected, config)

    @deprecated
    def test_from_cli_parser_options(self):
        parser = ArgumentParser()
        parser.add_argument("positional", type=int)
        parser.add_argument("--flag", action="store_true")

        cli = ConfigParser(JSONIO(), parser=parser)
        conf, ns = cli.parse_config(["5", "--flag"])
        self.assertEqual(Namespace(positional=5, flag=True), ns)
        self.assertDictEqual({}, dict(conf))

    @deprecated
    def test_from_cli_parser_options_overrides(self):
        parser = ArgumentParser()
        parser.add_argument("positional", type=int)
        parser.add_argument("--flag", action="store_true")

        k, v = "key", "value"
        cli = ConfigParser(JSONIO(), parser=parser)
        conf, ns = cli.parse_config(["--flag", "5", "=".join([k, v])])
        self.assertEqual(Namespace(positional=5, flag=True), ns)
        self.assertDictEqual({k: v}, dict(conf))
