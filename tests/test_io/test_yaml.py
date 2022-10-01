from io import StringIO

from upsilonconf.io.yaml import *
from .test_base import Utils


class TestYAMLIO(Utils.TestConfigIO):
    @staticmethod
    def generate_file_content():
        yield "foo: 1"
        yield "bar: test"
        yield "baz:"
        yield "  a: 0.1"
        yield "  b: 0.2"

    @staticmethod
    def default_io():
        return YAMLIO()

    def test_write_indent(self):
        indent_io = YAMLIO(indent=4)
        buffer = StringIO()
        indent_io.write_to(buffer, Utils.CONFIG)
        buffer.seek(0)
        contents = self.file_contents.replace(" " * 2, " " * 4)
        self.assertMultiLineEqual(contents, buffer.getvalue().rstrip())

    def test_write_sort_keys(self):
        d = dict(Utils.CONFIG["baz"])
        sorted_lines = sorted(
            [line[2:] for line in self.generate_file_content() if line.startswith("  ")]
        )
        assert len(d) > 1 and len(d) == len(sorted_lines), "invalid test setup"

        sorted_io = YAMLIO(sort_keys=True)
        buffer = StringIO()
        sorted_io.write_to(buffer, d)
        buffer.seek(0)
        for expected in sorted_lines:
            self.assertEqual(expected, next(buffer).rstrip())

        buffer = StringIO()
        sorted_io.write_to(buffer, {k: d[k] for k in reversed(d)})
        buffer.seek(0)
        for expected in sorted_lines:
            self.assertEqual(expected, next(buffer).rstrip())

    def test_float_parsing(self):
        for expression in ("1.3e-5", "1e5", ".5e3"):
            buffer = StringIO("foo: " + expression)
            config = YAMLIO().read_from(buffer)
            self.assertEqual(float(expression), config["foo"])
