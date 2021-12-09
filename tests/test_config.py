import copy
import doctest
from unittest import TestCase

import upsilonconf.config
from upsilonconf.config import Configuration
from upsilonconf.errors import InvalidKeyError


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(upsilonconf.config))
    return tests


class TestConfiguration(TestCase):

    KWARGS = {"a": 1, "b": "foo", "c": None, "d": object()}

    def setUp(self):
        self.empty_config = Configuration()
        self.simple_config = Configuration(a=1, b=2, c=3)
        self.complex_config = Configuration(foo=69, bar="test", sub=self.simple_config)

    def test_constructor(self):
        c = Configuration(**self.KWARGS)

        for k, v in self.KWARGS.items():
            self.assertIn(k, c.keys())
            self.assertIn(v, c.values())
            self.assertEqual(v, c[k])

    def test_constructor_sub(self):
        c = Configuration(sub=self.KWARGS)

        self.assertIsInstance(c.sub, Configuration)
        for k, v in self.KWARGS.items():
            self.assertEqual(v, c.sub[k])

    def test_constructor_copy(self):
        c = Configuration(**self.simple_config)

        for k, v in self.simple_config.items():
            self.assertEqual(v, c[k])

        del c[k]
        self.assertNotIn(k, c, msg="bad test")
        self.assertIn(k, self.simple_config)

    def test_repr(self):
        self.assertEqual(self.empty_config, eval(repr(self.empty_config)))
        self.assertEqual(self.simple_config, eval(repr(self.simple_config)))
        self.assertEqual(self.complex_config, eval(repr(self.complex_config)))

    def test_str(self):
        self.assertEqual("{}", str(self.empty_config))

        for conf in (self.simple_config, self.complex_config):
            _str = str(conf)
            self.assertTrue(_str.startswith("{"))
            self.assertTrue(_str.endswith("}"))
            for k, v in conf.items():
                self.assertIn(str(k), _str)
                self.assertIn(str(v), _str)

    def test_serialisation(self):
        import pickle

        serial = pickle.dumps(self.complex_config)
        config = pickle.loads(serial)
        self.assertNotIn(b"_content", serial)
        self.assertEqual(self.complex_config, config)

    def test_copy(self):
        self.empty_config["key"] = []
        new_config = copy.copy(self.empty_config)
        self.assertIsNot(new_config, self.empty_config)
        self.assertEqual(new_config, self.empty_config)
        self.assertIs(new_config["key"], self.empty_config["key"])

    def test_deepcopy(self):
        self.empty_config["key"] = []
        new_config = copy.deepcopy(self.empty_config)
        self.assertIsNot(new_config, self.empty_config)
        self.assertEqual(new_config, self.empty_config)
        self.assertIsNot(new_config["key"], self.empty_config["key"])

    # # # Mapping Interface # # #

    def test_getitem(self):
        for k, v in self.simple_config.items():
            self.assertEqual(v, self.simple_config[k])

    def test_getitem_invalid(self):
        k = "ridiculous"
        with self.assertRaises(KeyError):
            _ = self.empty_config[k]

        self.assertNotIn(k, self.simple_config, msg="bad test")
        with self.assertRaises(KeyError):
            _ = self.simple_config[k]

    def test_getitem_tuple(self):
        for k, v in self.simple_config.items():
            self.assertEqual(v, self.complex_config["sub", k])

    def test_getitem_tuple_invalid(self):
        k = "ridiculous"
        with self.assertRaisesRegex(KeyError, "'sub'"):
            _ = self.empty_config["sub", k]

        self.assertNotIn(k, self.simple_config, msg="bad test")
        with self.assertRaisesRegex(KeyError, f"'{k}'"):
            _ = self.complex_config["sub", k]

    def test_getitem_dotted(self):
        for k, v in self.simple_config.items():
            self.assertEqual(v, self.complex_config[".".join(["sub", k])])

    def test_getitem_dotted_invalid(self):
        k = "ridiculous"
        with self.assertRaisesRegex(KeyError, "'sub'"):
            _ = self.empty_config[".".join(["sub", k])]

        self.assertNotIn(k, self.simple_config, msg="bad test")
        with self.assertRaisesRegex(KeyError, f"'{k}'"):
            _ = self.complex_config[".".join(["sub", k])]

    def test_setitem(self):
        k, v = "ridiculous", 69
        self.empty_config[k] = v
        self.assertIn(k, self.empty_config.keys())
        self.assertEqual(v, self.empty_config[k])

        self.assertNotIn(k, self.simple_config, msg="bad test")
        self.simple_config[k] = v
        self.assertIn(k, self.simple_config.keys())
        self.assertEqual(v, self.simple_config[k])

    def test_setitem_invalid_key(self):
        with self.assertRaisesRegex(InvalidKeyError, "letter"):
            self.empty_config[""] = None

        with self.assertRaisesRegex(InvalidKeyError, "letter"):
            self.empty_config["_bla"] = None

        with self.assertRaisesRegex(InvalidKeyError, "symbol"):
            self.empty_config["bla*x"] = None

        with self.assertRaisesRegex(InvalidKeyError, "special"):
            self.empty_config["overwrite"] = None

    def test_setitem_overwrite(self):
        k = next(iter(self.simple_config.keys()))
        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.simple_config[k] = None

    def test_setitem_dict(self):
        k, v = "sub", {"a": 1, "b": 2}
        self.empty_config[k] = v
        self.assertIn(k, self.empty_config.keys())
        self.assertIsInstance(self.empty_config[k], Configuration)
        for _k, _v in v.items():
            self.assertEqual(_v, self.empty_config[k][_k])

    def test_setitem_dict_invalid_key(self):
        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.complex_config["sub"] = dict(**self.simple_config)

    def test_setitem_tuple(self):
        k, v = "ridiculous", 69
        self.complex_config["sub", k] = v
        self.assertIn(k, self.complex_config["sub"].keys())
        self.assertEqual(v, self.complex_config["sub"][k])

        self.empty_config[k, k] = v
        self.assertIn(k, self.empty_config.keys())
        self.assertIsInstance(self.empty_config[k], Configuration)
        self.assertIn(k, self.empty_config[k].keys())
        self.assertEqual(v, self.empty_config[k, k])

    def test_setitem_tuple_invalid_key(self):
        k = next(iter(self.simple_config.keys()))
        with self.assertRaisesRegex(KeyError, k):
            self.simple_config[k, k + "_sub"] = None

        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.complex_config["sub", k] = None

    def test_setitem_dotted(self):
        k, v = "ridiculous", 69
        self.complex_config[".".join(["sub", k])] = v
        self.assertIn(k, self.complex_config["sub"].keys())
        self.assertEqual(v, self.complex_config["sub"][k])

        self.empty_config[".".join([k, k])] = v
        self.assertIn(k, self.empty_config.keys())
        self.assertIsInstance(self.empty_config[k], Configuration)
        self.assertIn(k, self.empty_config[k].keys())
        self.assertEqual(v, self.empty_config[k, k])

    def test_setitem_dotted_invalid_key(self):
        k = next(iter(self.simple_config.keys()))
        with self.assertRaisesRegex(KeyError, k):
            self.simple_config[".".join([k, k + "_sub"])] = None

        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.complex_config[".".join(["sub", k])] = None

    def test_setitem_recursion(self):
        self.empty_config["recursion"] = self.empty_config
        self.assertIsNot(self.empty_config, self.empty_config["recursion"])

        self.complex_config["recursion"] = self.complex_config
        self.assertIsNot(self.complex_config, self.empty_config["recursion"])
        self.assertIsNot(
            self.complex_config["sub"], self.complex_config["recursion"]["sub"]
        )

    def test_delitem(self):
        for k in list(self.simple_config.keys()):
            del self.simple_config[k]
            self.assertNotIn(k, self.simple_config)
        self.assertEqual(0, len(self.simple_config))

    def test_delitem_invalid(self):
        k = "ridiculous"
        with self.assertRaises(KeyError):
            del self.empty_config[k]

        self.assertNotIn(k, self.simple_config, msg="bad test")
        with self.assertRaises(KeyError):
            del self.simple_config[k]

    def test_delitem_tuple(self):
        for k in self.simple_config.keys():
            del self.complex_config["sub", k]
            self.assertNotIn(k, self.complex_config["sub"])
        self.assertIn("sub", self.complex_config)

    def test_delitem_tuple_invalid(self):
        k = "ridiculous"
        with self.assertRaisesRegex(KeyError, "'sub'"):
            del self.empty_config["sub", k]

        self.assertNotIn(k, self.simple_config, msg="bad test")
        with self.assertRaisesRegex(KeyError, f"'{k}'"):
            del self.complex_config["sub", k]

    def test_delitem_dotted(self):
        for k in self.simple_config.keys():
            del self.complex_config[".".join(["sub", k])]
            self.assertNotIn(k, self.complex_config["sub"])
        self.assertIn("sub", self.complex_config)

    def test_delitem_dotted_invalid(self):
        k = "ridiculous"
        with self.assertRaisesRegex(KeyError, "'sub'"):
            del self.empty_config[".".join(["sub", k])]

        self.assertNotIn(k, self.simple_config, msg="bad test")
        with self.assertRaisesRegex(KeyError, f"'{k}'"):
            del self.complex_config[".".join(["sub", k])]

    def test_iter(self):
        with self.assertRaises(StopIteration):
            next(iter(self.empty_config))

        history = []
        iterator = iter(self.simple_config)
        for k in iterator:
            self.assertIn(k, self.simple_config)
            self.assertNotIn(k, history)
            history.append(k)

        with self.assertRaises(StopIteration):
            next(iterator)

    def test_length(self):
        self.assertEqual(0, len(self.empty_config))
        self.assertEqual(3, len(self.simple_config))
        self.assertEqual(3, len(self.complex_config))

    # # # Attribute Access # # #

    def test_getattr(self):
        meth = getattr(self.empty_config, "overwrite")
        self.assertEqual(self.empty_config.overwrite, meth)

        for k, v in self.simple_config.items():
            self.assertEqual(v, getattr(self.simple_config, k))

        for k, v in self.simple_config.items():
            self.assertEqual(v, getattr(self.complex_config.sub, k))

    def test_getattr_invalid(self):
        with self.assertRaisesRegex(AttributeError, "config"):
            _ = self.empty_config.ridiculous

        with self.assertRaisesRegex(AttributeError, "no attribute"):
            _ = self.empty_config._ridiculous

        with self.assertRaisesRegex(AttributeError, "no attribute"):
            _ = getattr(self.empty_config, "1234")

    def test_setattr(self):
        k, v = "ridiculous", 69
        setattr(self.empty_config, k, v)
        self.assertIn(k, self.empty_config.keys())
        self.assertEqual(v, self.empty_config[k])

    def test_setattr_invalid_key(self):
        k, v = "_ridiculous", 69
        setattr(self.empty_config, k, v)
        self.assertNotIn(k, self.empty_config.keys())
        self.assertEqual(v, getattr(self.empty_config, k))

    def test_setattr_overwrite(self):
        k = next(iter(self.simple_config.keys()))
        with self.assertRaisesRegex(AttributeError, "overwrite"):
            setattr(self.simple_config, k, None)

    def test_delattr(self):
        for k in list(self.simple_config.keys()):
            delattr(self.complex_config.sub, k)
            self.assertIsNone(getattr(self.complex_config.sub, k, None))

        for k in list(self.simple_config.keys()):
            delattr(self.simple_config, k)
            self.assertIsNone(getattr(self.simple_config, k, None))

    def test_delattr_invalid(self):
        with self.assertRaisesRegex(AttributeError, "config"):
            del self.empty_config.ridiculous

        with self.assertRaisesRegex(AttributeError, "no attribute"):
            del self.empty_config._ridiculous

        with self.assertRaisesRegex(AttributeError, "no attribute"):
            delattr(self.empty_config, "1234")

    def test_dir(self):
        _dir = dir(self.simple_config)
        self.assertIn("overwrite", _dir)
        for k in self.simple_config.keys():
            self.assertIn(k, _dir)

    # # # Other Stuff # # #

    def test_overwrite(self):
        new_val = "bla"
        for k in self.simple_config.keys():
            self.simple_config.overwrite(k, new_val)
            self.assertEqual(self.simple_config[k], new_val)

    def test_overwrite_invalid(self):
        with self.assertRaises(KeyError):
            self.empty_config.overwrite("ridiculous", None)

    def test_overwrite_tuple(self):
        new_val = "bla"
        for k in self.simple_config.keys():
            self.complex_config.overwrite(["sub", k], new_val)
            self.assertEqual(self.complex_config["sub", k], new_val)

    def test_overwrite_tuple_invalid(self):
        with self.assertRaises(KeyError):
            self.empty_config.overwrite(["sub", "ridiculous"], None)

    def test_overwrite_dotted(self):
        new_val = "bla"
        for k in self.simple_config.keys():
            self.complex_config.overwrite(".".join(["sub", k]), new_val)
            self.assertEqual(self.complex_config["sub", k], new_val)

    def test_overwrite_dotted_invalid(self):
        with self.assertRaises(KeyError):
            self.empty_config.overwrite(".".join(["sub", "ridiculous"]), None)
