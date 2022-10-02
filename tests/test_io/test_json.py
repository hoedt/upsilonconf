from io import StringIO

from upsilonconf.io.json import *
from .test_base import Utils


class TestJSONIO(Utils.TestConfigIO):
    @staticmethod
    def generate_file_content():
        yield "{"
        yield '  "foo": 1,'
        yield '  "bar": "test",'
        yield '  "baz": {'
        yield '    "a": 0.1,'
        yield '    "b": 0.2'
        yield "  }"
        yield "}"

    @staticmethod
    def default_io():
        return JSONIO()

    def test_extensions(self):
        self.assertIn(".json", self.io.extensions)

    def test_write_indent(self):
        indent_io = JSONIO(indent=4)
        buffer = StringIO()
        indent_io.write_to(buffer, Utils.CONFIG)
        buffer.seek(0)
        contents = self.file_contents.replace(" " * 2, " " * 4)
        self.assertMultiLineEqual(contents, buffer.getvalue().rstrip())

    def test_write_sort_keys(self):
        d = dict(Utils.CONFIG["baz"])
        keys = list(d)
        sorted_lines = sorted(
            [
                line[2:]
                for line in self.generate_file_content()
                if line.startswith("    ")
            ]
        )
        assert len(d) > 1 and len(d) == len(sorted_lines), "invalid test setup"
        sorted_lines = ["{"] + sorted_lines + ["}"]

        sorted_io = JSONIO(sort_keys=True)
        buffer = StringIO()
        sorted_io.write_to(buffer, {k: d[k] for k in keys})
        buffer.seek(0)
        for expected in sorted_lines:
            self.assertEqual(expected, next(buffer).rstrip())

        buffer = StringIO()
        sorted_io.write_to(buffer, {k: d[k] for k in reversed(keys)})
        buffer.seek(0)
        for expected in sorted_lines:
            self.assertEqual(expected, next(buffer).rstrip())
