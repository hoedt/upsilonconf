import copy
import doctest
from unittest import TestCase

import upsilonconf.config
from upsilonconf.config import *


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(upsilonconf.config))
    return tests


class TestConfiguration(TestCase):
    def setUp(self):
        self.empty_config = Configuration()
        self.simple_config = Configuration(a=1, b=2, c=3)
        self.complex_config = Configuration(foo=69, bar="test", sub=self.simple_config)

    def test_constructor(self):
        KWARGS = {"a": 1, "b": "foo", "c": None, "d": object()}
        c = Configuration(**KWARGS)

        for k, v in KWARGS.items():
            self.assertIn(k, c.keys())
            self.assertIn(v, c.values())
            self.assertEqual(v, c[k])

    def test_constructor_sub(self):
        KWARGS = {"a": 1, "b": "foo", "c": None, "d": object()}
        c = Configuration(sub=KWARGS)

        self.assertIsInstance(c.sub, Configuration)
        for k, v in KWARGS.items():
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

    def test_getitem_invalid_key_type(self):
        with self.assertRaises(TypeError):
            _ = self.simple_config[1]

        with self.assertRaises(TypeError):
            _ = self.simple_config[1, 2, 3]

        with self.assertRaises(TypeError):
            _ = self.simple_config[object()]

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
        with self.assertWarns(UserWarning) as cm:
            self.empty_config[""] = None
        self.assertEqual(1, len(cm.warnings))

        with self.assertRaisesRegex(InvalidKeyError, "letter"):
            self.empty_config["_bla"] = None

        with self.assertWarns(UserWarning) as cm:
            self.empty_config["bla*x"] = None
        self.assertEqual(1, len(cm.warnings))

        with self.assertRaisesRegex(InvalidKeyError, "interface"):
            self.empty_config["overwrite"] = None

        with self.assertWarns(UserWarning) as cm:
            self.empty_config["def"] = None
        self.assertEqual(1, len(cm.warnings))

    def test_setitem_invalid_key_type(self):
        with self.assertRaises(TypeError):
            self.simple_config[1] = None

        with self.assertRaises(TypeError):
            self.simple_config[1, 2, 3] = None

        with self.assertRaises(TypeError):
            self.simple_config[object()] = None

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

    def test_delitem_invalid_key_type(self):
        with self.assertRaises(TypeError):
            del self.simple_config[1]

        with self.assertRaises(TypeError):
            del self.simple_config[1, 2, 3]

        with self.assertRaises(TypeError):
            del self.simple_config[object()]

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

    # # # Merging # # #

    def test_union(self):
        expected = dict(self.complex_config)
        expected.update(**self.simple_config)

        union = self.complex_config | self.simple_config
        self.assertIsNot(union, self.complex_config)
        self.assertIsNot(union, self.simple_config)
        self.assertDictEqual(dict(union), expected)

    def test_union_empty(self):
        union = self.simple_config | self.empty_config
        self.assertIsNot(union, self.simple_config)
        self.assertIsNot(union, self.empty_config)
        self.assertDictEqual(dict(self.simple_config), dict(union))

    def test_union_overlap(self):
        _k, _v = next(iter(self.simple_config)), []
        other = Configuration(**{_k: _v, _k + "_duplicate": _v})

        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.simple_config | other

    def test_union_subconfig(self):
        _k, _v = next(iter(self.simple_config)), []
        other = Configuration(sub={_k: _v, _k + "_duplicate": _v})

        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.complex_config | other

    def test_union_dict(self):
        other = dict(self.simple_config)
        expected = dict(self.complex_config)
        expected.update(**other)

        union = self.complex_config | other
        self.assertIsNot(union, self.complex_config)
        self.assertIsNot(union, other)
        self.assertDictEqual(dict(union), expected)

    def test_union_dict_dotted(self):
        other = dict({"sub.test": None})
        expected = Configuration(**self.simple_config)
        for k, v in other.items():
            expected[k] = v

        union = self.simple_config | other
        self.assertIsNot(union, self.simple_config)
        self.assertIsNot(union, other)
        self.assertDictEqual(dict(union), dict(expected))

    def test_union_dict_overlap(self):
        _k, _v = next(iter(self.simple_config)), []
        other = {_k: _v, _k + "_duplicate": _v}

        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.simple_config | other

    def test_union_dict_subconfig(self):
        _k, _v = next(iter(self.simple_config)), []
        other = {"sub": {_k: _v, _k + "_duplicate": _v}}

        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.complex_config | other

    def test_union_dict_subconfig_dotted(self):
        _k, _v = next(iter(self.simple_config)), []
        other = {".".join(["sub", k]): _v for k in (_k, _k + "_duplicate")}

        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.complex_config | other

    def test_union_dict_flipped(self):
        other = dict(self.simple_config)
        expected = dict(other)
        expected.update(**self.complex_config)

        union = other | self.complex_config
        self.assertIsNot(union, other)
        self.assertIsNot(union, self.complex_config)
        self.assertDictEqual(dict(union), expected)

    def test_union_dict_flipped_dotted(self):
        other = dict({"sub.test": None})
        expected = Configuration(**self.simple_config)
        for k, v in other.items():
            expected[k] = v

        union = other | self.simple_config
        self.assertIsNot(union, other)
        self.assertIsNot(union, self.simple_config)
        self.assertDictEqual(dict(union), dict(expected))

    def test_union_dict_flipped_overlap(self):
        _k, _v = next(iter(self.simple_config)), []
        other = {_k: _v, _k + "_duplicate": _v}

        with self.assertRaisesRegex(ValueError, "overwrite"):
            other | self.simple_config

    def test_union_dict_flipped_subconfig(self):
        _k, _v = next(iter(self.simple_config)), []
        other = {"sub": {_k: _v, _k + "_duplicate": _v}}

        with self.assertRaisesRegex(ValueError, "overwrite"):
            other | self.complex_config

    def test_union_dict_flipped_subconfig_dotted(self):
        _k, _v = next(iter(self.simple_config)), []
        other = {".".join(["sub", k]): _v for k in (_k, _k + "_duplicate")}

        with self.assertRaisesRegex(ValueError, "overwrite"):
            other | self.complex_config

    def test_union_inplace(self):
        old_ref = self.complex_config
        expected = dict(self.complex_config)
        expected.update(**self.simple_config)

        self.complex_config |= self.simple_config
        self.assertIs(old_ref, self.complex_config)
        self.assertDictEqual(dict(self.complex_config), expected)

    def test_union_inplace_dict(self):
        other = dict(self.simple_config)
        old_ref = self.complex_config
        expected = dict(**self.complex_config)
        expected.update(**other)

        self.complex_config |= other
        self.assertIs(old_ref, self.complex_config)
        self.assertDictEqual(dict(self.complex_config), expected)

    def test_union_inplace_overlap(self):
        with self.assertRaisesRegex(ValueError, "key"):
            self.simple_config |= self.simple_config

    def test_union_dict_inplace_overlap(self):
        with self.assertRaisesRegex(ValueError, "key"):
            self.simple_config |= dict(self.simple_config)

    # # # Attribute Access # # #

    def test_getattr(self):
        meth = getattr(self.empty_config, "overwrite")
        self.assertEqual(self.empty_config.overwrite, meth)

        for k, v in self.simple_config.items():
            self.assertEqual(v, getattr(self.simple_config, k))

        for k, v in self.simple_config.items():
            self.assertEqual(v, getattr(self.complex_config.sub, k))

    def test_getattr_invalid(self):
        with self.assertRaisesRegex(AttributeError, "object has no attribute"):
            _ = self.empty_config.ridiculous

        with self.assertRaisesRegex(AttributeError, "object has no attribute"):
            _ = self.empty_config._ridiculous

        with self.assertRaisesRegex(AttributeError, "object has no attribute"):
            _ = getattr(self.empty_config, "1234")

    def test_setattr(self):
        k, v = "ridiculous", 69
        setattr(self.empty_config, k, v)
        self.assertIn(k, self.empty_config.keys())
        self.assertEqual(v, self.empty_config[k])

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
        with self.assertRaisesRegex(AttributeError, "ridiculous"):
            del self.empty_config.ridiculous

        with self.assertRaisesRegex(AttributeError, "_ridiculous"):
            del self.empty_config._ridiculous

        with self.assertRaisesRegex(AttributeError, "1234"):
            delattr(self.empty_config, "1234")

    def test_dir(self):
        _dir = dir(self.simple_config)
        self.assertIn("overwrite", _dir)
        for k in self.simple_config.keys():
            self.assertIn(k, _dir)

    # # # Other Stuff # # #

    def test_overwrite(self):
        new_val = "bla"
        for k, v in self.simple_config.items():
            old_val = self.simple_config.overwrite(k, new_val)
            self.assertEqual(v, old_val)
            self.assertEqual(self.simple_config[k], new_val)

    def test_overwrite_existing(self):
        new_key, new_val = "ridiculous", "bla"
        old_val = self.empty_config.overwrite(new_key, new_val)
        self.assertIsNone(old_val)
        self.assertEqual(self.empty_config[new_key], new_val)

    def test_overwrite_tuple(self):
        new_val = "bla"
        for k, v in self.simple_config.items():
            old_val = self.complex_config.overwrite(["sub", k], new_val)
            self.assertEqual(v, old_val)
            self.assertEqual(self.complex_config["sub", k], new_val)

    def test_overwrite_tuple_existing(self):
        new_key, new_val = "ridiculous", "bla"
        old_val = self.empty_config.overwrite(["sub", new_key], new_val)
        self.assertIsNone(old_val)
        self.assertEqual(self.empty_config["sub", new_key], new_val)

    def test_overwrite_dotted(self):
        new_val = "bla"
        for k, v in self.simple_config.items():
            old_val = self.complex_config.overwrite(".".join(["sub", k]), new_val)
            self.assertEqual(v, old_val)
            self.assertEqual(self.complex_config["sub", k], new_val)

    def test_overwrite_dotted_existing(self):
        new_key, new_val = "ridiculous", "bla"
        old_val = self.empty_config.overwrite(".".join(["sub", new_key]), new_val)
        self.assertIsNone(old_val)
        self.assertEqual(self.empty_config["sub", new_key], new_val)

    def test_overwrite_order(self):
        new_val = "bla"
        key_order = tuple(self.simple_config.keys())
        for k, v in self.simple_config.items():
            old_val = self.simple_config.overwrite(k, new_val)
            self.assertEqual(v, old_val)
            self.assertEqual(self.simple_config[k], new_val)
            self.assertTupleEqual(key_order, tuple(self.simple_config.keys()))

    def test_overwrite_all(self):
        base_config = self.complex_config
        expected = dict(base_config)
        expected.update(**self.simple_config)

        overwritten = base_config.overwrite_all(self.simple_config)
        self.assertDictEqual({k: None for k in self.simple_config}, overwritten)
        self.assertDictEqual(dict(base_config), expected)

    def test_overwrite_all_kwargs(self):
        base_config = self.complex_config
        expected = dict(base_config)
        expected.update(**self.simple_config)

        overwritten = base_config.overwrite_all(**self.simple_config)
        self.assertDictEqual({k: None for k in self.simple_config}, overwritten)
        self.assertDictEqual(dict(base_config), expected)

    def test_overwrite_all_empty(self):
        expected = dict(self.simple_config)
        overwritten = self.simple_config.overwrite_all(self.empty_config)
        self.assertDictEqual({}, overwritten)
        self.assertDictEqual(dict(self.simple_config), expected)

    def test_overwrite_all_overlap(self):
        base_config = self.simple_config
        _k, _v = next(iter(self.simple_config)), []
        other = Configuration(**{_k: _v, _k + "_duplicate": _v})
        old_values = {k: base_config[_k] if k == _k else None for k in other}
        expected = dict(base_config)
        expected.update(**other)

        overwritten = base_config.overwrite_all(other)
        self.assertDictEqual(old_values, overwritten)
        self.assertDictEqual(dict(base_config), expected)

    def test_overwrite_all_subconfig(self):
        base_config = self.complex_config
        _k, _v = next(iter(self.simple_config)), []
        other = Configuration(sub={_k: _v, _k + "_duplicate": _v})
        old_values = {
            "sub": {
                k: base_config["sub"][_k] if k == _k else None for k in other["sub"]
            }
        }
        expected = dict(base_config["sub"])
        expected.update(**other["sub"])

        overwritten = base_config.overwrite_all(other)
        self.assertDictEqual(old_values, overwritten)
        self.assertDictEqual(dict(base_config["sub"]), expected)

    def test_overwrite_all_dict(self):
        base_config = self.complex_config
        other = dict(self.simple_config)
        expected = dict(base_config)
        expected.update(**other)

        overwritten = base_config.overwrite_all(other)
        self.assertDictEqual({k: None for k in other}, overwritten)
        self.assertDictEqual(dict(base_config), expected)

    def test_overwrite_all_dict_dotted(self):
        base_config = self.simple_config
        other = dict({"sub.test": 0})
        expected = Configuration(**base_config)
        for k, v in other.items():
            expected[k] = v

        overwritten = base_config.overwrite_all(other)
        self.assertDictEqual({k: None for k in other}, overwritten)
        self.assertDictEqual(dict(base_config), dict(expected))

    def test_overwrite_all_dict_overlap(self):
        base_config = self.simple_config
        _k, _v = next(iter(self.simple_config)), []
        other = {_k: _v, _k + "_duplicate": _v}
        old_values = {k: base_config[k] if k == _k else None for k in other}
        expected = dict(base_config)
        expected.update(**other)

        overwritten = base_config.overwrite_all(other)
        self.assertDictEqual(old_values, overwritten)
        self.assertDictEqual(dict(base_config), expected)

    def test_overwrite_all_dict_subconfig(self):
        base_config = self.complex_config
        _k, _v = next(iter(self.simple_config)), []
        other = {"sub": {_k: _v, _k + "_duplicate": _v}}
        old_values = {
            "sub": {
                k: base_config["sub"][_k] if k == _k else None for k in other["sub"]
            }
        }
        expected = dict(base_config["sub"])
        expected.update(**other["sub"])

        overwritten = base_config.overwrite_all(other)
        self.assertDictEqual(old_values, overwritten)
        self.assertDictEqual(dict(base_config["sub"]), expected)

    def test_overwrite_all_dict_subconfig_dotted(self):
        base_config = self.complex_config
        _k, _v = next(iter(self.simple_config)), []
        other = {".".join(["sub", k]): _v for k in (_k, _k + "_duplicate")}
        old_values = {
            k: base_config["sub"][_k] if k.endswith(_k) else None for k in other
        }
        expected = Configuration(**base_config)
        for k, v in other.items():
            expected.overwrite(k, v)

        overwritten = base_config.overwrite_all(other)
        self.assertDictEqual(old_values, overwritten)
        self.assertDictEqual(dict(base_config["sub"]), dict(expected["sub"]))

    # # # Dict Conversion # # #

    def test_from_dict(self):
        d = dict(self.simple_config)
        conf = Configuration.from_dict(d)
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(self.simple_config, conf)

    def test_from_dict_empty(self):
        conf = Configuration.from_dict({})
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(self.empty_config, conf)

    def test_from_dict_nested(self):
        d = dict(self.complex_config)
        d["sub"] = dict(d["sub"])
        conf = Configuration.from_dict(d)
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(self.complex_config, conf)

    def test_from_dict_key_modifiers(self):
        d = {"keyX1": "with X", "keyO2": "with O"}
        key_mods = {"X": "_", "O": "_minus_"}
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(key_1="with X", key_minus_2="with O")
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_neighbours(self):
        d = {"keyX1": "with X"}
        conf = Configuration.from_dict(d, {"X": "_", "1": "3"})
        ref = Configuration(key_3="with X")
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(ref, conf)

        conf = Configuration.from_dict(d, {"1": "3", "X": "_"})
        ref = Configuration(key_3="with X")
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_missing(self):
        d = {"key 1": "with space", "key-2": "with hyphen"}
        with self.assertWarns(UserWarning) as cm:
            Configuration.from_dict(d)

        self.assertEqual(2, len(cm.warnings))

    def test_from_dict_key_modifiers_combination(self):
        d = {"keyX1": "with X", "keyO2": "with O"}
        key_mods = {"X": "_", "O": "_minus_", "k": "K"}
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(Key_1="with X", Key_minus_2="with O")
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_order(self):
        d = {"keyX1": "with X", "keyO2": "with O"}
        key_mods = {"X": "0", "O": "_"}
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(key01="with X", key_2="with O")
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(ref, conf)

        key_mods = {"O": "_", "X": "0"}  # reversed
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(key01="with X", key_2="with O")
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_order_length(self):
        d = {"keyX1": "with X", "keyO2": "with O"}
        key_mods = {"keyX": "k", "keyO": "K", " X": "_", "O": "_"}
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(k1="with X", K2="with O")
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(ref, conf)

        key_mods = {"O": "_", "X": "A", "keyO": "K", "keyX": "k"}  # reversed
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(k1="with X", K2="with O")
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_nested(self):
        d = {"keyX1": "with X", "keyO2": {"keyO1": 1, "keyX2": 2}}
        key_mods = {"keyX": "k", "keyO": "K", " X": "_", "O": "_"}
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(k1="with X", K2=Configuration(K1=1, k2=2))
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(ref, conf)

        key_mods = {"O": "_", "X": "A", "keyO": "K", "keyX": "k"}  # reversed
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(k1="with X", K2=Configuration(K1=1, k2=2))
        self.assertIsInstance(conf, Configuration)
        self.assertEqual(ref, conf)

    def test_to_dict(self):
        d = self.simple_config.to_dict()
        d_ref = dict(self.simple_config)
        self.assertDictEqual(d_ref, d)

    def test_to_dict_empty(self):
        d = self.empty_config.to_dict()
        self.assertDictEqual({}, d)

    def test_to_dict_nested(self):
        d = self.complex_config.to_dict()
        d_ref = dict(self.complex_config)
        d_ref["sub"] = dict(self.complex_config.sub)
        self.assertDictEqual(d_ref["sub"], d["sub"])
        self.assertDictEqual(d_ref, d)

    def test_to_dict_flat(self):
        d = self.complex_config.to_dict(flat=True)
        d_ref = dict(self.complex_config)
        for k, v in d_ref.pop("sub").items():
            d_ref[f"sub.{k}"] = v
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers(self):
        conf = Configuration(key_1="with space", key02="with hyphen")
        d = conf.to_dict({"_": " ", "0": "-"})
        d_ref = {"key 1": "with space", "key-2": "with hyphen"}
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers_combination(self):
        conf = Configuration(key_1="with space", key02="with hyphen")
        d = conf.to_dict({"_": " ", "0": "-", "k": "K"})
        d_ref = {"Key 1": "with space", "Key-2": "with hyphen"}
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers_combination_neighbours(self):
        conf = Configuration(key_1="with space")
        d = conf.to_dict({"1": "3", "_": " "})
        d_ref = {"key 3": "with space"}
        self.assertDictEqual(d_ref, d)

        d = conf.to_dict({"_": " ", "1": "3"})
        d_ref = {"key 3": "with space"}
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers_order(self):
        conf = Configuration(key_1="with space", key02="with space")
        d = conf.to_dict({"0": "_", "_": " "})
        d_ref = {"key 1": "with space", "key_2": "with space"}
        self.assertDictEqual(d_ref, d)

        d = conf.to_dict({"_": " ", "0": "_"})  # key-mods reversed
        d_ref = {"key 1": "with space", "key_2": "with space"}
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers_order_length(self):
        conf = Configuration(key_1="with space", key_2="with hyphen")
        d = conf.to_dict({"_1": " 1", "_2": "-2", "_": "0"})
        d_ref = {"key 1": "with space", "key-2": "with hyphen"}
        self.assertDictEqual(d_ref, d)

        d = conf.to_dict({"_": "0", "_2": "-2", "_1": " 1"})  # key-mods reversed
        d_ref = {"key 1": "with space", "key-2": "with hyphen"}
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers_nested(self):
        conf = Configuration(key_1="with space", key_2=Configuration(key_1=1, key_2=2))
        d = conf.to_dict({"_1": " 1", "_2": "-2", "_": "0"})
        d_ref = {"key 1": "with space", "key-2": {"key 1": 1, "key-2": 2}}
        self.assertDictEqual(d_ref, d)

        d = conf.to_dict({"_": "0", "_2": "-2", "_1": " 1"})  # key-mods reversed
        d_ref = {"key 1": "with space", "key-2": {"key 1": 1, "key-2": 2}}
        self.assertEqual(d_ref, d)


class TestPlainConfiguration(TestCase):
    def test_constructor_empty(self):
        conf = PlainConfiguration()
        self.assertDictEqual({}, conf.__dict__)

    def test_constructor_single(self):
        conf = PlainConfiguration(a=123)
        self.assertDictEqual({"a": 123}, conf.__dict__)

    def test_constructor(self):
        KWARGS = {"a": 123, "b": "foo", "c": None, "d": object()}
        conf = PlainConfiguration(**KWARGS)
        self.assertDictEqual(KWARGS, conf.__dict__)

    def test_constructor_subconfig(self):
        sub = {"a": 123}
        conf = PlainConfiguration(sub=sub)
        self.assertEqual({"sub": PlainConfiguration(**sub)}, conf.__dict__)
        self.assertIsInstance(conf.__dict__["sub"], PlainConfiguration)

    def test_constructor_positional_arg(self):
        with self.assertRaises(TypeError, msg="positional args invalid"):
            PlainConfiguration({"a": 123})

    def test_repr_empty(self):
        conf = PlainConfiguration()
        self.assertEqual("PlainConfiguration()", repr(conf))

    def test_repr(self):
        conf = PlainConfiguration(a=123, b="foo", c=None)
        self.assertEqual(conf, eval(repr(conf)))

    def test_str_empty(self):
        conf = PlainConfiguration()
        self.assertEqual(str({}), str(conf))

    def test_str(self):
        conf = PlainConfiguration(a=123, b="foo", c=None)
        self.assertEqual("{a: 123, b: foo, c: None}", str(conf))
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        self.assertEqual("{sub: {a: 123}}", str(conf), msg="hierarchical")

    def test_eq_empty(self):
        self.assertEqual(PlainConfiguration(), PlainConfiguration())

    def test_eq(self):
        conf = PlainConfiguration(a=123, b=None)
        self.assertEqual(conf, PlainConfiguration(a=123, b=None))
        self.assertEqual(PlainConfiguration(a=123, b=None), conf, msg="symmetry")
        self.assertEqual(conf, PlainConfiguration(b=None, a=123), msg="ordering")
        self.assertNotEqual(conf, PlainConfiguration(a=123), msg="cardinality")
        self.assertNotEqual(
            conf, PlainConfiguration(ax=123, bx=None), msg="respect key"
        )
        self.assertNotEqual(
            conf, PlainConfiguration(a=234, b=None), msg="respect value"
        )
        self.assertNotEqual(
            conf, PlainConfiguration(a=None, b=123), msg="respect key-value"
        )
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration()),
            PlainConfiguration(sub=PlainConfiguration()),
            msg="hierarchical",
        )

    def test_eq_dict(self):
        conf = PlainConfiguration(a=123, b=None)
        self.assertEqual(conf, {"a": 123, "b": None})
        self.assertEqual({"a": 123, "b": None}, conf, msg="symmetry")
        self.assertEqual(conf, {"b": None, "a": 123}, msg="ordering")
        self.assertNotEqual(conf, {"a": 123}, msg="cardinality")
        self.assertNotEqual(conf, {"ax": 123, "bx": None}, msg="respect key")
        self.assertNotEqual(conf, {"a": 234, "b": None}, msg="respect value")
        self.assertNotEqual(conf, {"a": None, "b": 123}, msg="respect key-value")
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration()),
            PlainConfiguration(sub=PlainConfiguration()),
            msg="hierarchical",
        )

    def test_eq_invalid_types(self):
        conf = PlainConfiguration(a=123, b=None)
        self.assertNotEqual(conf, 123)
        self.assertNotEqual(conf, ["a", 123, "b", None])
        # TODO: equality with dataclasses?
        self.assertNotEqual(conf, type("tmp", (object,), {"a": 123, "b": None})())

    def test_copy(self):
        conf = PlainConfiguration(a=123, sub=PlainConfiguration())
        conf_copy = copy.copy(conf)
        self.assertIsNot(conf, conf_copy, msg="new object")
        self.assertEqual(conf, conf_copy, msg="respect equality")
        self.assertIs(conf["sub"], conf_copy["sub"], msg="copy superficial")

    def test_deepcopy(self):
        conf = PlainConfiguration(a=123, sub=PlainConfiguration())
        conf_copy = copy.deepcopy(conf)
        self.assertIsNot(conf, conf_copy, msg="new object")
        self.assertEqual(conf, conf_copy, msg="respect equality")
        self.assertIsNot(conf["sub"], conf_copy["sub"], msg="copy deep")

    def test_serialisation(self):
        import pickle

        conf = PlainConfiguration(a=123, b="foo", sub=PlainConfiguration())
        serial = pickle.dumps(conf)
        reconstructed = pickle.loads(serial)
        self.assertEqual(conf, reconstructed)

    # # # Mapping Interface # # #

    def test_getitem(self):
        conf = PlainConfiguration(a=[123], b="foo")
        self.assertEqual([123], conf["a"])
        self.assertIs(getattr(conf, "a"), conf["a"], msg="dict/attr consistency")
        self.assertEqual("foo", conf["b"])
        self.assertIs(getattr(conf, "b"), conf["b"], msg="dict/attr consistency")

    def test_getitem_invalid(self):
        conf = PlainConfiguration(a=123)
        with self.assertRaisesRegex(KeyError, "b"):
            _ = conf["b"]

    def test_getitem_invalid_key_type(self):
        conf = PlainConfiguration(a=123)
        with self.assertRaisesRegex(TypeError, "string", msg="int indexing"):
            _ = conf[1]
        with self.assertRaisesRegex(TypeError, "string", msg="obj indexing"):
            _ = conf[object()]
        with self.assertRaisesRegex(TypeError, "string", msg="int-tuple indexing"):
            _ = conf[1, 2, 3]

        with self.assertRaisesRegex(TypeError, "tuple", msg="set indexing"):
            _ = conf[{"a"}]
        with self.assertRaisesRegex(TypeError, "tuple", msg="list indexing"):
            _ = conf[["a"]]

    def test_getitem_class_attributes(self):
        conf = PlainConfiguration()
        with self.assertRaisesRegex(KeyError, "__dict__"):
            _ = conf["__dict__"]
        with self.assertRaisesRegex(KeyError, "items"):
            _ = conf["items"]

    def test_getitem_dotted(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=[123]))
        self.assertEqual([123], conf["sub.a"])
        self.assertIs(conf["sub"]["a"], conf["sub.a"], msg="consistency")

    def test_getitem_dotted_invalid(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        with self.assertRaisesRegex(KeyError, "b", msg="bad subconfig key"):
            _ = conf["sub.b"]
        with self.assertRaisesRegex(KeyError, "x", msg="bad subconfig"):
            _ = conf["x.b"]

    def test_getitem_tuple(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=[123]))
        self.assertEqual([123], conf["sub", "a"])
        self.assertIs(conf["sub"]["a"], conf["sub", "a"], msg="consistency")

    def test_getitem_tuple_invalid(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        with self.assertRaisesRegex(KeyError, "b", msg="bad subconfig key"):
            _ = conf["sub", "b"]
        with self.assertRaisesRegex(KeyError, "x", msg="bad subconfig"):
            _ = conf["x", "b"]

    def test_setitem(self):
        conf = PlainConfiguration()
        conf["a"] = 123
        conf["b"] = "foo"
        self.assertDictEqual({"a": 123, "b": "foo"}, conf.__dict__)

    def test_setitem_overwrite(self):
        conf = PlainConfiguration(a=123, b="foo")
        conf["a"] = 234
        conf["b"] = "bar"
        self.assertDictEqual({"a": 234, "b": "bar"}, conf.__dict__)

    def test_setitem_dict(self):
        conf = PlainConfiguration()
        conf["sub"] = {"a": 123}
        self.assertDictEqual({"sub": PlainConfiguration(a=123)}, conf.__dict__)
        self.assertIsInstance(conf["sub"], PlainConfiguration)

    def test_setitem_dict_overwrite(self):
        conf = PlainConfiguration(sub=Configuration(a=123))
        conf["sub"] = {"b": "foo"}
        self.assertDictEqual({"sub": PlainConfiguration(b="foo")}, conf.__dict__)
        self.assertIsInstance(conf["sub"], PlainConfiguration)

    def test_setitem_invalid_key_type(self):
        conf = PlainConfiguration()
        with self.assertRaisesRegex(TypeError, "string", msg="int indexing"):
            conf[1] = 123
        with self.assertRaisesRegex(TypeError, "string", msg="obj indexing"):
            conf[object()] = 123
        with self.assertRaisesRegex(TypeError, "string", msg="int-tuple indexing"):
            conf[1, 2, 3] = 123

        with self.assertRaisesRegex(TypeError, "tuple", msg="set indexing"):
            conf[{"a"}] = 123
        with self.assertRaisesRegex(TypeError, "tuple", msg="list indexing"):
            conf[["a"]] = [123]

    def test_setitem_class_attributes(self):
        conf = PlainConfiguration()
        conf["__dict__"] = 123
        conf["items"] = "foo"
        self.assertDictEqual({"__dict__": 123, "items": "foo"}, conf.__dict__)

    def test_get_setitem_class_attributes(self):
        conf = PlainConfiguration()
        conf["__dict__"] = 123
        self.assertEqual(123, conf["__dict__"])

    def test_del_setitem_class_attributes(self):
        conf = PlainConfiguration()
        conf["__dict__"] = 123
        del conf["__dict__"]
        self.assertDictEqual({}, conf.__dict__)

    def test_setitem_dotted(self):
        conf = PlainConfiguration(sub=PlainConfiguration())
        conf["sub.a"] = 123
        self.assertDictEqual({"a": 123}, conf["sub"].__dict__)

    def test_setitem_dotted_overwrite(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        conf["sub.a"] = 234
        self.assertDictEqual({"a": 234}, conf["sub"].__dict__)

    def test_setitem_dotted_create_subconfig(self):
        conf = PlainConfiguration()
        conf["sub.a"] = 123
        self.assertDictEqual({"sub": PlainConfiguration(a=123)}, conf.__dict__)
        self.assertIsInstance(conf["sub"], PlainConfiguration)

    def test_setitem_tuple(self):
        conf = PlainConfiguration(sub=PlainConfiguration())
        conf["sub", "a"] = 123
        self.assertDictEqual({"a": 123}, conf["sub"].__dict__)

    def test_setitem_tuple_overwrite(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        conf["sub", "a"] = 234
        self.assertDictEqual({"a": 234}, conf["sub"].__dict__)

    def test_setitem_tuple_create_subconfig(self):
        conf = PlainConfiguration()
        conf["sub", "a"] = 123
        self.assertDictEqual({"sub": PlainConfiguration(a=123)}, conf.__dict__)
        self.assertIsInstance(conf["sub"], PlainConfiguration)

    def test_delitem(self):
        conf = PlainConfiguration(a=[123], b="foo")
        del conf["a"]
        self.assertDictEqual({"b": "foo"}, conf.__dict__)

    def test_delitem_invalid(self):
        conf = PlainConfiguration(a=123)
        with self.assertRaisesRegex(KeyError, "b"):
            del conf["b"]

    def test_delitem_invalid_key_type(self):
        conf = PlainConfiguration(a=123)
        with self.assertRaisesRegex(TypeError, "string", msg="int indexing"):
            _ = conf[1]
        with self.assertRaisesRegex(TypeError, "string", msg="obj indexing"):
            _ = conf[object()]
        with self.assertRaisesRegex(TypeError, "string", msg="int-tuple indexing"):
            _ = conf[1, 2, 3]

        with self.assertRaisesRegex(TypeError, "tuple", msg="set indexing"):
            _ = conf[{"a"}]
        with self.assertRaisesRegex(TypeError, "tuple", msg="list indexing"):
            _ = conf[["a"]]

    def test_delitem_class_attributes(self):
        conf = PlainConfiguration()
        with self.assertRaisesRegex(KeyError, "__dict__"):
            del conf["__dict__"]
        with self.assertRaisesRegex(KeyError, "items"):
            del conf["items"]

    def test_delitem_dotted(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=[123]))
        del conf["sub.a"]
        self.assertDictEqual({}, conf["sub"].__dict__)

    def test_delitem_dotted_invalid(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        with self.assertRaisesRegex(KeyError, "b", msg="bad subconfig key"):
            del conf["sub.b"]
        with self.assertRaisesRegex(KeyError, "x", msg="bad subconfig"):
            del conf["x.b"]

    def test_delitem_tuple(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=[123]))
        del conf["sub", "a"]
        self.assertDictEqual({}, conf["sub"].__dict__)

    def test_delitem_tuple_invalid(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        with self.assertRaisesRegex(KeyError, "b", msg="bad subconfig key"):
            del conf["sub", "b"]
        with self.assertRaisesRegex(KeyError, "x", msg="bad subconfig"):
            del conf["x", "b"]

    def test_iter(self):
        conf = PlainConfiguration(a=123, sub=PlainConfiguration(b="foo", c=None))
        conf_iter = iter(conf)
        self.assertEqual("a", next(conf_iter))
        self.assertEqual("sub", next(conf_iter))
        with self.assertRaises(StopIteration):
            next(conf_iter)

        conf = PlainConfiguration(sub=PlainConfiguration(b="foo", c=None), a=123)
        conf_iter = iter(conf)
        self.assertEqual("sub", next(conf_iter))
        self.assertEqual("a", next(conf_iter))
        with self.assertRaises(StopIteration):
            next(conf_iter)

    def test_length(self):
        self.assertEqual(0, len(PlainConfiguration()))
        self.assertEqual(1, len(PlainConfiguration(a=123)))
        self.assertEqual(
            2, len(PlainConfiguration(a=123, sub=PlainConfiguration(b="foo", c=None)))
        )

    def test_update_subconfig(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        conf.update(sub=PlainConfiguration(b="foo"))
        self.assertEqual(PlainConfiguration(sub=PlainConfiguration(b="foo")), conf)

    # # # Attribute Interface # # #

    def test_getattr(self):
        conf = PlainConfiguration(a=[123], b="foo")
        self.assertEqual([123], getattr(conf, "a"))
        self.assertIs(conf["a"], getattr(conf, "a"), msg="dict/attr consistency")
        self.assertEqual("foo", getattr(conf, "b"))
        self.assertIs(conf["b"], getattr(conf, "b"), msg="dict/attr consistency")

    def test_getattr_invalid(self):
        conf = PlainConfiguration(a=123)
        with self.assertRaisesRegex(AttributeError, "b"):
            _ = getattr(conf, "b")

    def test_getattr_invalid_key_type(self):
        conf = PlainConfiguration(a=123)
        with self.assertRaisesRegex(TypeError, "string", msg="int attr"):
            _ = getattr(conf, 1)
        with self.assertRaisesRegex(TypeError, "string", msg="obj attr"):
            _ = getattr(conf, object())
        with self.assertRaisesRegex(TypeError, "string", msg="int-tuple attr"):
            _ = getattr(conf, (1, 2, 3))
        with self.assertRaisesRegex(TypeError, "string", msg="set attr"):
            _ = getattr(conf, ("a",))
        with self.assertRaisesRegex(TypeError, "string", msg="set attr"):
            _ = getattr(conf, {"a"})
        with self.assertRaisesRegex(TypeError, "string", msg="list attr"):
            _ = getattr(conf, ["a"])

    def test_getattr_class_attributes(self):
        conf = PlainConfiguration()
        self.assertIs(getattr(conf, "__dict__"), conf.__dict__)
        self.assertEqual(getattr(conf, "items"), conf.items)

    def test_getattr_dotted(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=[123]))
        with self.assertRaisesRegex(AttributeError, "dot-string"):
            _ = getattr(conf, "sub.a")

    def test_setattr(self):
        conf = PlainConfiguration()
        setattr(conf, "a", 123)
        setattr(conf, "b", "foo")
        self.assertDictEqual({"a": 123, "b": "foo"}, conf.__dict__)

    def test_setattr_dict(self):
        conf = PlainConfiguration()
        setattr(conf, "sub", {"a": 123})
        self.assertDictEqual({"sub": PlainConfiguration(a=123)}, conf.__dict__)
        self.assertIsInstance(conf["sub"], PlainConfiguration)

    def test_setattr_invalid_key_type(self):
        conf = PlainConfiguration()
        with self.assertRaisesRegex(TypeError, "string", msg="int attr"):
            setattr(conf, 1, 123)
        with self.assertRaisesRegex(TypeError, "string", msg="obj attr"):
            setattr(conf, object(), 123)
        with self.assertRaisesRegex(TypeError, "string", msg="int-tuple attr"):
            setattr(conf, (1, 2, 3), 123)
        with self.assertRaisesRegex(TypeError, "string", msg="str-tuple attr"):
            setattr(conf, ("a",), 123)
        with self.assertRaisesRegex(TypeError, "string", msg="set attr"):
            setattr(conf, {"a"}, 123)
        with self.assertRaisesRegex(TypeError, "string", msg="list attr"):
            setattr(conf, ["a"], [123])

    def test_setatrr_class_attributes(self):
        conf = PlainConfiguration()
        with self.assertRaises(TypeError):
            setattr(conf, "__dict__", 123)

        setattr(conf, "items", "foo")
        self.assertDictEqual({"items": "foo"}, conf.__dict__)

    def test_get_setattr_class_attributes(self):
        conf = PlainConfiguration()
        setattr(conf, "items", 123)
        self.assertEqual(123, getattr(conf, "items"))

    def test_del_setattr_class_attributes(self):
        conf = PlainConfiguration()
        setattr(conf, "items", 123)
        delattr(conf, "items")
        self.assertDictEqual({}, conf.__dict__)

    def test_setattr_dotted(self):
        conf = PlainConfiguration(sub=PlainConfiguration())
        with self.assertRaisesRegex(AttributeError, "dot-string"):
            setattr(conf, "sub.a", 123)

    def test_delattr(self):
        conf = PlainConfiguration(a=[123], b="foo")
        delattr(conf, "a")
        self.assertDictEqual({"b": "foo"}, conf.__dict__)

    def test_delatrr_invalid(self):
        conf = PlainConfiguration(a=123)
        with self.assertRaisesRegex(AttributeError, "b"):
            delattr(conf, "b")

    def test_delattr_invalid_key_type(self):
        conf = PlainConfiguration(a=123)
        with self.assertRaisesRegex(TypeError, "string", msg="int attr"):
            delattr(conf, 1)
        with self.assertRaisesRegex(TypeError, "string", msg="obj attr"):
            delattr(conf, object())
        with self.assertRaisesRegex(TypeError, "string", msg="int-tuple attr"):
            delattr(conf, (1, 2, 3))
        with self.assertRaisesRegex(TypeError, "string", msg="set attr"):
            delattr(conf, ("a",))
        with self.assertRaisesRegex(TypeError, "string", msg="set attr"):
            delattr(conf, {"a"})
        with self.assertRaisesRegex(TypeError, "string", msg="list attr"):
            delattr(conf, ["a"])

    def test_delattr_class_attributes(self):
        conf = PlainConfiguration()
        delattr(conf, "__dict__")
        self.assertDictEqual({}, conf.__dict__)
        with self.assertRaisesRegex(AttributeError, "items"):
            delattr(conf, "items")

    def test_delattr_dotted(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=[123]))
        with self.assertRaisesRegex(AttributeError, "dot-string"):
            delattr(conf, "sub.a")

    def test_dir(self):
        conf = PlainConfiguration(a=123, b="foo", c=None, d=object())
        expected = sorted(dir(PlainConfiguration) + ["a", "b", "c", "d"])
        self.assertSequenceEqual(expected, dir(conf))

    # # # Merging # # #

    def test_union(self):
        conf1 = PlainConfiguration(a=123)
        conf2 = PlainConfiguration(b="foo")
        self.assertEqual(PlainConfiguration(a=123, b="foo"), conf1 | conf2)
        self.assertEqual(
            PlainConfiguration(a=123, b="foo"), conf2 | conf1, msg="symmetry"
        )
        self.assertIsNot(conf1 | conf2, conf1, msg="new object")
        self.assertIsNot(conf1 | conf2, conf2, msg="new object")

    def test_union_empty(self):
        conf = PlainConfiguration(a=123)
        self.assertEqual(conf, conf | PlainConfiguration())
        self.assertEqual(conf, PlainConfiguration() | conf, msg="symmetry")
        self.assertIsNot(conf | PlainConfiguration(), conf, msg="new object")

    def test_union_overlap(self):
        conf1 = PlainConfiguration(a=123, b="foo")
        conf2 = PlainConfiguration(b="bar", c=None)
        self.assertEqual(PlainConfiguration(a=123, b="bar", c=None), conf1 | conf2)
        self.assertEqual(PlainConfiguration(a=123, b="foo", c=None), conf2 | conf1)

    def test_union_subconfig(self):
        conf1 = PlainConfiguration(sub=PlainConfiguration(a=123))
        conf2 = PlainConfiguration(sub=PlainConfiguration(b="foo"))
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration(a=123, b="foo")), conf1 | conf2
        )
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration(a=123, b="foo")),
            conf2 | conf1,
            msg="symmetry",
        )
        self.assertIsNot((conf1 | conf2)["sub"], conf1["sub"], msg="new subconfig")
        self.assertIsNot((conf1 | conf2)["sub"], conf2["sub"], msg="new subconfig")

    def test_union_subconfig_value(self):
        conf1 = PlainConfiguration(sub=123)
        conf2 = PlainConfiguration(sub=PlainConfiguration(b="foo"))
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration(b="foo")), conf1 | conf2
        )
        self.assertEqual(
            PlainConfiguration(sub=123),
            conf2 | conf1,
            msg="symmetry",
        )

    def test_union_inplace(self):
        conf = PlainConfiguration(a=123)
        conf |= PlainConfiguration(b="foo")
        self.assertEqual(PlainConfiguration(a=123, b="foo"), conf)

    def test_union_inplace_empty(self):
        conf = PlainConfiguration(a=123)
        conf |= PlainConfiguration()
        self.assertEqual(PlainConfiguration(a=123), conf)

    def test_union_inplace_overlap(self):
        conf = PlainConfiguration(a=123, b="foo")
        conf |= PlainConfiguration(b="bar", c=None)
        self.assertEqual(PlainConfiguration(a=123, b="bar", c=None), conf)

    def test_union_inplace_subconfig(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        sub_old = conf["sub"]
        conf |= PlainConfiguration(sub=PlainConfiguration(b="foo"))
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration(a=123, b="foo")), conf
        )
        self.assertEqual(
            PlainConfiguration(a=123, b="foo"), sub_old, msg="hierarchical"
        )

    def test_union_inplace_subconfig_value(self):
        conf = PlainConfiguration(sub=123)
        conf |= PlainConfiguration(sub=PlainConfiguration(b="foo"))
        self.assertEqual(PlainConfiguration(sub=PlainConfiguration(b="foo")), conf)

        conf |= PlainConfiguration(sub=123)
        self.assertEqual(PlainConfiguration(sub=123), conf)

    def test_union_dict(self):
        conf = PlainConfiguration(a=123)
        d = {"b": "foo"}
        self.assertEqual(PlainConfiguration(a=123, b="foo"), conf | d)
        self.assertEqual(PlainConfiguration(a=123, b="foo"), d | conf, msg="symmetry")
        self.assertIsNot(conf | d, conf, msg="new object")

    def test_union_dict_empty(self):
        conf = PlainConfiguration(a=123)
        self.assertEqual(conf, conf | {})
        self.assertEqual(conf, {} | conf, msg="symmetry")
        self.assertIsNot(conf | {}, conf, msg="new object")

    def test_union_dict_overlap(self):
        conf = PlainConfiguration(a=123, b="foo")
        d = {"b": "bar", "c": None}
        self.assertEqual(PlainConfiguration(a=123, b="bar", c=None), conf | d)
        self.assertEqual(PlainConfiguration(a=123, b="foo", c=None), d | conf)

    def test_union_dict_subconfig(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        d = {"sub": {"b": "foo"}}
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration(a=123, b="foo")), conf | d
        )
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration(a=123, b="foo")),
            d | conf,
            msg="symmetry",
        )

    def test_union_dict_subconfig_value(self):
        conf = PlainConfiguration(sub=123)
        d = {"sub": {"b": "foo"}}
        self.assertEqual(PlainConfiguration(sub=PlainConfiguration(b="foo")), conf | d)
        self.assertEqual(
            PlainConfiguration(sub=123),
            d | conf,
            msg="symmetry",
        )

    def test_union_dict_dotted_subconfig(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        d = {"sub.b": "foo"}
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration(a=123, b="foo")), conf | d
        )
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration(a=123, b="foo")),
            d | conf,
            msg="symmetry",
        )

    def test_union_dict_dotted_create_subconfig(self):
        conf = PlainConfiguration()
        d = {"sub.b": "foo"}
        self.assertEqual(PlainConfiguration(sub=PlainConfiguration(b="foo")), conf | d)
        self.assertEqual(
            PlainConfiguration(sub=PlainConfiguration(b="foo")),
            d | conf,
            msg="symmetry",
        )

    # # # Conversions # # #

    def test_from_dict(self):
        conf = PlainConfiguration.from_dict({"a": 123, "b": "foo"})
        self.assertEqual(PlainConfiguration(a=123, b="foo"), conf)

    def test_from_dict_empty(self):
        conf = PlainConfiguration.from_dict({})
        self.assertEqual(PlainConfiguration(), conf)

    def test_from_dict_subconfig(self):
        conf = PlainConfiguration.from_dict({"sub": {"a": 123}})
        self.assertEqual(PlainConfiguration(sub=PlainConfiguration(a=123)), conf)

    def test_to_dict(self):
        conf = PlainConfiguration(a=123, b="foo")
        self.assertDictEqual({"a": 123, "b": "foo"}, conf.to_dict())

    def test_to_dict_empty(self):
        conf = PlainConfiguration()
        self.assertDictEqual({}, conf.to_dict())

    def test_to_dict_subconfig(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        self.assertDictEqual({"sub": {"a": 123}}, conf.to_dict())
