import copy
import doctest
from unittest import TestCase

import upsilonconf.config
from upsilonconf.config import Configuration, InvalidKeyError


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
        with self.assertRaisesRegex(InvalidKeyError, "letter"):
            self.empty_config[""] = None

        with self.assertRaisesRegex(InvalidKeyError, "letter"):
            self.empty_config["_bla"] = None

        with self.assertRaisesRegex(InvalidKeyError, "symbol"):
            self.empty_config["bla*x"] = None

        with self.assertRaisesRegex(InvalidKeyError, "special"):
            self.empty_config["overwrite"] = None

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
        self.assertEqual(self.simple_config, conf)

    def test_from_dict_empty(self):
        conf = Configuration.from_dict({})
        self.assertEqual(self.empty_config, conf)

    def test_from_dict_nested(self):
        d = dict(self.complex_config)
        d["sub"] = dict(d["sub"])
        conf = Configuration.from_dict(d)
        self.assertEqual(self.complex_config, conf)

    def test_from_dict_key_modifiers(self):
        d = {"key 1": "with space", "key-2": "with hyphen"}
        key_mods = {" ": "_", "-": "_minus_"}
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(key_1="with space", key_minus_2="with hyphen")
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_missing(self):
        d = {"key 1": "with space", "key-2": "with hyphen"}
        with self.assertRaises(ValueError):
            Configuration.from_dict(d)

    def test_from_dict_key_modifiers_combination(self):
        d = {"key 1": "with space", "key-2": "with hyphen"}
        key_mods = {" ": "_", "-": "_minus_", "k": "K"}
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(Key_1="with space", Key_minus_2="with hyphen")
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_order(self):
        d = {"key 1": "with space", "key-2": "with hyphen"}
        key_mods = {" ": "0", "-": "_"}
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(key01="with space", key_2="with hyphen")
        self.assertEqual(ref, conf)

        key_mods = {"-": "_", " ": "-"}  # reversed
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(key01="with space", key_2="with hyphen")
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_order_length(self):
        d = {"key 1": "with space", "key-2": "with hyphen"}
        key_mods = {"key ": "k", "key-": "K", "  ": "_", "-": "_"}
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(k1="with space", K2="with hyphen")
        self.assertEqual(ref, conf)

        key_mods = {"-": "_", " ": "-", "key-": "K", "key ": "k"}  # reversed
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(k1="with space", K2="with hyphen")
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_nested(self):
        d = {"key 1": "with space", "key-2": {"key-1": 1, "key 2": 2}}
        key_mods = {"key ": "k", "key-": "K", "  ": "_", "-": "_"}
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(k1="with space", K2=Configuration(K1=1, k2=2))
        self.assertEqual(ref, conf)

        key_mods = {"-": "_", " ": "-", "key-": "K", "key ": "k"}  # reversed
        conf = Configuration.from_dict(d, key_mods)
        ref = Configuration(k1="with space", K2=Configuration(K1=1, k2=2))
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
