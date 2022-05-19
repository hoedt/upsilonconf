from unittest import TestCase

from upsilonconf.utils.optional_dependency import OptionalDependencyError
from upsilonconf.utils.optional_dependency import optional_dependency_to


IMPORT_KEY = "import"


def import_valid(*args, **kwargs):
    import sys

    kwargs[IMPORT_KEY] = sys
    return args, kwargs


def import_invalid(*args, **kwargs):
    import sys.invalid

    kwargs[IMPORT_KEY] = sys.invalid
    return args, kwargs


class Test(TestCase):
    def test_optional_dependency_to(self):
        wrapper = optional_dependency_to()
        _import_valid = wrapper(import_valid)
        args, kwargs = _import_valid()
        self.assertTupleEqual((), args)
        self.assertIn(IMPORT_KEY, kwargs)

    def test_optional_dependency_to_import_error(self):
        wrapper = optional_dependency_to()
        _import_invalid = wrapper(import_invalid)
        with self.assertRaisesRegex(OptionalDependencyError, "install '.*' to"):
            _import_invalid()

    def test_optional_dependency_to_with_arguments(self):
        wrapper = optional_dependency_to()
        _import_valid = wrapper(import_valid)
        args, kwargs = (1, "test", object()), {"kwarg1": 1, "kwarg2": 0.2}
        _args, _kwargs = _import_valid(*args, **kwargs)
        self.assertTupleEqual(args, _args)
        self.assertIn(IMPORT_KEY, _kwargs)
        _kwargs.pop(IMPORT_KEY)
        self.assertEqual(kwargs, _kwargs)

    def test_optional_dependency_to_import_error_with_arguments(self):
        wrapper = optional_dependency_to()
        _import_invalid = wrapper(import_invalid)
        args, kwargs = (1, "test", object()), {"kwarg1": 1, "kwarg2": 0.2}
        with self.assertRaisesRegex(OptionalDependencyError, "install '.*' to"):
            _import_invalid(args, kwargs)

    def test_optional_dependency_to_message(self):
        msg = "test imports"
        wrapper = optional_dependency_to(msg)
        _import_valid = wrapper(import_valid)
        args, kwargs = _import_valid()
        self.assertTupleEqual((), args)
        self.assertIn(IMPORT_KEY, kwargs)

    def test_optional_dependency_to_import_error_message(self):
        msg = "test imports"
        wrapper = optional_dependency_to(msg)
        _import_invalid = wrapper(import_invalid)
        with self.assertRaisesRegex(OptionalDependencyError, msg):
            _import_invalid()

    def test_optional_dependency_to_package(self):
        pkg = "sys-invalid"
        wrapper = optional_dependency_to(package=pkg)
        _import_valid = wrapper(import_valid)
        args, kwargs = _import_valid()
        self.assertTupleEqual((), args)
        self.assertIn(IMPORT_KEY, kwargs)

    def test_optional_dependency_to_import_error_package(self):
        pkg = "sys-invalid"
        wrapper = optional_dependency_to(package=pkg)
        _import_invalid = wrapper(import_invalid)
        with self.assertRaisesRegex(OptionalDependencyError, f"install '{pkg}' to"):
            _import_invalid()
