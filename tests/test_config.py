import copy
import doctest
from typing import Type
from unittest import TestCase

import upsilonconf.config
from upsilonconf.config import *


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(upsilonconf.config))
    return tests


class TestCarefulConfiguration(TestCase):
    def setUp(self):
        self.empty_config = CarefulConfiguration()
        self.simple_config = CarefulConfiguration(a=1, b=2, c=3)
        self.complex_config = CarefulConfiguration(
            foo=69, bar="test", sub=self.simple_config
        )

    def test_constructor(self):
        KWARGS = {"a": 1, "b": "foo", "c": None, "d": object()}
        c = CarefulConfiguration(**KWARGS)

        for k, v in KWARGS.items():
            self.assertIn(k, c.keys())
            self.assertIn(v, c.values())
            self.assertEqual(v, c[k])

    def test_constructor_sub(self):
        KWARGS = {"a": 1, "b": "foo", "c": None, "d": object()}
        c = CarefulConfiguration(sub=KWARGS)

        self.assertIsInstance(c.sub, CarefulConfiguration)
        for k, v in KWARGS.items():
            self.assertEqual(v, c.sub[k])

    def test_constructor_copy(self):
        c = CarefulConfiguration(**self.simple_config)

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
        self.assertIsInstance(self.empty_config[k], CarefulConfiguration)
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
        self.assertIsInstance(self.empty_config[k], CarefulConfiguration)
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
        self.assertIsInstance(self.empty_config[k], CarefulConfiguration)
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
        other = CarefulConfiguration(**{_k: _v, _k + "_duplicate": _v})

        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.simple_config | other

    def test_union_subconfig(self):
        _k, _v = next(iter(self.simple_config)), []
        other = CarefulConfiguration(sub={_k: _v, _k + "_duplicate": _v})

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
        expected = CarefulConfiguration(**self.simple_config)
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
        expected = CarefulConfiguration(**self.simple_config)
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
        other = CarefulConfiguration(**{_k: _v, _k + "_duplicate": _v})
        old_values = {k: base_config[_k] if k == _k else None for k in other}
        expected = dict(base_config)
        expected.update(**other)

        overwritten = base_config.overwrite_all(other)
        self.assertDictEqual(old_values, overwritten)
        self.assertDictEqual(dict(base_config), expected)

    def test_overwrite_all_subconfig(self):
        base_config = self.complex_config
        _k, _v = next(iter(self.simple_config)), []
        other = CarefulConfiguration(sub={_k: _v, _k + "_duplicate": _v})
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
        expected = CarefulConfiguration(**base_config)
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
        expected = CarefulConfiguration(**base_config)
        for k, v in other.items():
            expected.overwrite(k, v)

        overwritten = base_config.overwrite_all(other)
        self.assertDictEqual(old_values, overwritten)
        self.assertDictEqual(dict(base_config["sub"]), dict(expected["sub"]))

    # # # Dict Conversion # # #

    def test_from_dict(self):
        d = dict(self.simple_config)
        conf = CarefulConfiguration.from_dict(d)
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(self.simple_config, conf)

    def test_from_dict_empty(self):
        conf = CarefulConfiguration.from_dict({})
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(self.empty_config, conf)

    def test_from_dict_nested(self):
        d = dict(self.complex_config)
        d["sub"] = dict(d["sub"])
        conf = CarefulConfiguration.from_dict(d)
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(self.complex_config, conf)

    def test_from_dict_key_modifiers(self):
        d = {"keyX1": "with X", "keyO2": "with O"}
        key_mods = {"X": "_", "O": "_minus_"}
        conf = CarefulConfiguration.from_dict(d, key_mods)
        ref = CarefulConfiguration(key_1="with X", key_minus_2="with O")
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_neighbours(self):
        d = {"keyX1": "with X"}
        conf = CarefulConfiguration.from_dict(d, {"X": "_", "1": "3"})
        ref = CarefulConfiguration(key_3="with X")
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(ref, conf)

        conf = CarefulConfiguration.from_dict(d, {"1": "3", "X": "_"})
        ref = CarefulConfiguration(key_3="with X")
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_missing(self):
        d = {"key 1": "with space", "key-2": "with hyphen"}
        with self.assertWarns(UserWarning) as cm:
            CarefulConfiguration.from_dict(d)

        self.assertEqual(2, len(cm.warnings))

    def test_from_dict_key_modifiers_combination(self):
        d = {"keyX1": "with X", "keyO2": "with O"}
        key_mods = {"X": "_", "O": "_minus_", "k": "K"}
        conf = CarefulConfiguration.from_dict(d, key_mods)
        ref = CarefulConfiguration(Key_1="with X", Key_minus_2="with O")
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_order(self):
        d = {"keyX1": "with X", "keyO2": "with O"}
        key_mods = {"X": "0", "O": "_"}
        conf = CarefulConfiguration.from_dict(d, key_mods)
        ref = CarefulConfiguration(key01="with X", key_2="with O")
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(ref, conf)

        key_mods = {"O": "_", "X": "0"}  # reversed
        conf = CarefulConfiguration.from_dict(d, key_mods)
        ref = CarefulConfiguration(key01="with X", key_2="with O")
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_order_length(self):
        d = {"keyX1": "with X", "keyO2": "with O"}
        key_mods = {"keyX": "k", "keyO": "K", " X": "_", "O": "_"}
        conf = CarefulConfiguration.from_dict(d, key_mods)
        ref = CarefulConfiguration(k1="with X", K2="with O")
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(ref, conf)

        key_mods = {"O": "_", "X": "A", "keyO": "K", "keyX": "k"}  # reversed
        conf = CarefulConfiguration.from_dict(d, key_mods)
        ref = CarefulConfiguration(k1="with X", K2="with O")
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(ref, conf)

    def test_from_dict_key_modifiers_nested(self):
        d = {"keyX1": "with X", "keyO2": {"keyO1": 1, "keyX2": 2}}
        key_mods = {"keyX": "k", "keyO": "K", " X": "_", "O": "_"}
        conf = CarefulConfiguration.from_dict(d, key_mods)
        ref = CarefulConfiguration(k1="with X", K2=CarefulConfiguration(K1=1, k2=2))
        self.assertIsInstance(conf, CarefulConfiguration)
        self.assertEqual(ref, conf)

        key_mods = {"O": "_", "X": "A", "keyO": "K", "keyX": "k"}  # reversed
        conf = CarefulConfiguration.from_dict(d, key_mods)
        ref = CarefulConfiguration(k1="with X", K2=CarefulConfiguration(K1=1, k2=2))
        self.assertIsInstance(conf, CarefulConfiguration)
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
        conf = CarefulConfiguration(key_1="with space", key02="with hyphen")
        d = conf.to_dict({"_": " ", "0": "-"})
        d_ref = {"key 1": "with space", "key-2": "with hyphen"}
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers_combination(self):
        conf = CarefulConfiguration(key_1="with space", key02="with hyphen")
        d = conf.to_dict({"_": " ", "0": "-", "k": "K"})
        d_ref = {"Key 1": "with space", "Key-2": "with hyphen"}
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers_combination_neighbours(self):
        conf = CarefulConfiguration(key_1="with space")
        d = conf.to_dict({"1": "3", "_": " "})
        d_ref = {"key 3": "with space"}
        self.assertDictEqual(d_ref, d)

        d = conf.to_dict({"_": " ", "1": "3"})
        d_ref = {"key 3": "with space"}
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers_order(self):
        conf = CarefulConfiguration(key_1="with space", key02="with space")
        d = conf.to_dict({"0": "_", "_": " "})
        d_ref = {"key 1": "with space", "key_2": "with space"}
        self.assertDictEqual(d_ref, d)

        d = conf.to_dict({"_": " ", "0": "_"})  # key-mods reversed
        d_ref = {"key 1": "with space", "key_2": "with space"}
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers_order_length(self):
        conf = CarefulConfiguration(key_1="with space", key_2="with hyphen")
        d = conf.to_dict({"_1": " 1", "_2": "-2", "_": "0"})
        d_ref = {"key 1": "with space", "key-2": "with hyphen"}
        self.assertDictEqual(d_ref, d)

        d = conf.to_dict({"_": "0", "_2": "-2", "_1": " 1"})  # key-mods reversed
        d_ref = {"key 1": "with space", "key-2": "with hyphen"}
        self.assertDictEqual(d_ref, d)

    def test_to_dict_key_modifiers_nested(self):
        conf = CarefulConfiguration(
            key_1="with space", key_2=CarefulConfiguration(key_1=1, key_2=2)
        )
        d = conf.to_dict({"_1": " 1", "_2": "-2", "_": "0"})
        d_ref = {"key 1": "with space", "key-2": {"key 1": 1, "key-2": 2}}
        self.assertDictEqual(d_ref, d)

        d = conf.to_dict({"_": "0", "_2": "-2", "_1": " 1"})  # key-mods reversed
        d_ref = {"key 1": "with space", "key-2": {"key 1": 1, "key-2": 2}}
        self.assertEqual(d_ref, d)


class TestConfiguration(TestCase):
    def test_deprecation(self):
        with self.assertWarns(DeprecationWarning):
            Configuration()


class Utils:
    class TestConfigurationBase(TestCase):
        @property
        def config_class(self) -> Type[ConfigurationBase]:
            raise NotImplementedError()

        def test_constructor_empty(self):
            conf = self.config_class()
            self.assertDictEqual({}, conf.__dict__)

        def test_constructor_single(self):
            conf = self.config_class(a=123)
            self.assertDictEqual({"a": 123}, conf.__dict__)

        def test_constructor(self):
            KWARGS = {"a": 123, "b": "foo", "c": None, "d": object()}
            conf = self.config_class(**KWARGS)
            self.assertDictEqual(KWARGS, conf.__dict__)

        def test_constructor_subconfig(self):
            sub = {"a": 123}
            conf = self.config_class(sub=sub)
            self.assertEqual({"sub": self.config_class(**sub)}, conf.__dict__)
            self.assertIsInstance(conf.__dict__["sub"], self.config_class)

        def test_constructor_dot_string(self):
            conf = self.config_class(**{"sub.a": 123})
            self.assertDictEqual({"sub": {"a": 123}}, conf.__dict__)

        def test_constructor_tuple(self):
            with self.assertRaises(TypeError):
                self.config_class({("sub", "a"): 123})

        def test_constructor_positional_arg(self):
            with self.assertRaises(TypeError, msg="positional args invalid"):
                self.config_class({"a": 123})

        def test_constructor_dot_string_subconfig(self):
            conf = self.config_class(**{"sub.a": 123, "sub.b": "foo"})
            self.assertDictEqual({"sub": {"a": 123, "b": "foo"}}, conf.__dict__)

        def test_constructor_dot_string_overwrite_subconfig(self):
            conf = self.config_class(sub=self.config_class(a=123), **{"sub.a": 234})
            self.assertDictEqual({"sub": {"a": 234}}, conf.__dict__)

        def test_constructor_subconfig_overwrite_dot_string(self):
            conf = self.config_class(sub=self.config_class(a=123), **{"sub.a": 234})
            self.assertDictEqual({"sub": {"a": 234}}, conf.__dict__)

        def test_repr_empty(self):
            conf = self.config_class()
            self.assertEqual(f"{conf.__class__.__name__}()", repr(conf))

        def test_repr(self):
            conf = self.config_class(a=123, b="foo", c=None)
            self.assertEqual(conf, eval(repr(conf)))

        def test_str_empty(self):
            conf = self.config_class()
            self.assertEqual(str({}), str(conf))

        def test_str(self):
            conf = self.config_class(a=123, b="foo", c=None)
            self.assertEqual("{a: 123, b: foo, c: None}", str(conf))
            conf = self.config_class(sub=self.config_class(a=123))
            self.assertEqual("{sub: {a: 123}}", str(conf), msg="hierarchical")

        def test_eq_empty(self):
            conf = self.config_class()
            self.assertEqual(conf, conf, msg="identity")
            self.assertEqual(conf, self.config_class())

        def test_eq(self):
            conf = self.config_class(a=123, b=None)
            self.assertEqual(conf, conf, msg="identity")
            self.assertEqual(conf, self.config_class(a=123, b=None))
            self.assertEqual(self.config_class(a=123, b=None), conf, msg="symmetry")
            self.assertEqual(conf, self.config_class(b=None, a=123), msg="ordering")
            self.assertNotEqual(conf, self.config_class(a=123), msg="cardinality")
            self.assertNotEqual(
                conf, self.config_class(ax=123, bx=None), msg="respect key"
            )
            self.assertNotEqual(
                conf, self.config_class(a=234, b=None), msg="respect value"
            )
            self.assertNotEqual(
                conf, self.config_class(a=None, b=123), msg="respect key-value"
            )

        def test_eq_hierarchical(self):
            conf = self.config_class(sub=PlainConfiguration(a=123))
            self.assertEqual(conf, conf, msg="identity")
            self.assertEqual(conf, self.config_class(sub=PlainConfiguration(a=123)))
            self.assertNotEqual(
                conf,
                self.config_class(sub=self.config_class(a=234)),
                msg="respect value",
            )
            self.assertNotEqual(
                conf,
                self.config_class(other=self.config_class(a=123)),
                msg="respect key",
            )

        def test_eq_dict(self):
            conf = self.config_class(a=123, b=None)
            self.assertEqual(conf, {"a": 123, "b": None})
            self.assertEqual({"a": 123, "b": None}, conf, msg="symmetry")
            self.assertEqual(conf, {"b": None, "a": 123}, msg="ordering")
            self.assertNotEqual(conf, {"a": 123}, msg="cardinality")
            self.assertNotEqual(conf, {"ax": 123, "bx": None}, msg="respect key")
            self.assertNotEqual(conf, {"a": 234, "b": None}, msg="respect value")
            self.assertNotEqual(conf, {"a": None, "b": 123}, msg="respect key-value")

        def test_eq_dict_hierarchical(self):
            conf = self.config_class(sub=self.config_class(a=123))
            self.assertEqual(conf, {"sub": {"a": 123}})
            self.assertNotEqual(conf, {"sub": {"a": 234}}, msg="respect value")
            self.assertNotEqual(conf, {"other": {"a": 123}}, msg="respect key")

        def test_eq_invalid_types(self):
            conf = self.config_class(a=123, b=None)
            self.assertNotEqual(conf, 123)
            self.assertNotEqual(conf, ["a", 123, "b", None])
            # TODO: equality with dataclasses?
            self.assertNotEqual(conf, type("tmp", (object,), {"a": 123, "b": None})())

        def test_hash(self):
            with self.assertRaises(TypeError):
                hash(self.config_class())

        def test_copy(self):
            conf = self.config_class(a=123, sub=self.config_class())
            conf_copy = copy.copy(conf)
            self.assertIsNot(conf, conf_copy, msg="new object")
            self.assertEqual(conf, conf_copy, msg="respect equality")
            self.assertIs(conf["sub"], conf_copy["sub"], msg="copy superficial")

        def test_deepcopy(self):
            conf = self.config_class(a=123, sub=self.config_class())
            conf_copy = copy.deepcopy(conf)
            self.assertIsNot(conf, conf_copy, msg="new object")
            self.assertEqual(conf, conf_copy, msg="respect equality")
            self.assertIsNot(conf["sub"], conf_copy["sub"], msg="copy deep")

        def test_serialisation(self):
            import pickle

            conf = self.config_class(a=123, b="foo", sub=self.config_class())
            serial = pickle.dumps(conf)
            reconstructed = pickle.loads(serial)
            self.assertEqual(conf, reconstructed)

        # # # Attribute Interface # # #

        def test_getattr(self):
            conf = self.config_class(a=123, b="foo")
            self.assertEqual(123, getattr(conf, "a"))
            self.assertIs(conf["a"], getattr(conf, "a"), msg="dict/attr consistency")
            self.assertEqual("foo", getattr(conf, "b"))
            self.assertIs(conf["b"], getattr(conf, "b"), msg="dict/attr consistency")

        def test_getattr_invalid(self):
            conf = self.config_class(a=123)
            with self.assertRaisesRegex(AttributeError, "b"):
                _ = getattr(conf, "b")

        def test_getattr_invalid_key_type(self):
            conf = self.config_class(a=123)
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
            conf = self.config_class()
            self.assertIs(getattr(conf, "__dict__"), conf.__dict__)
            self.assertIs(getattr(conf, "__class__"), self.config_class)
            self.assertEqual(getattr(conf, "items"), conf.items)

        def test_getattr_dotted(self):
            conf = self.config_class(sub=self.config_class(a=[123]))
            with self.assertRaisesRegex(AttributeError, "dot-string"):
                _ = getattr(conf, "sub.a")

        def test_dir(self):
            conf = self.config_class(a=123, b="foo", c=None, d=object())
            expected = sorted(dir(self.config_class) + ["a", "b", "c", "d"])
            self.assertSequenceEqual(expected, dir(conf))

        # # # Mapping Interface # # #

        def test_getitem(self):
            conf = self.config_class(a=123, b="foo")
            self.assertEqual(123, conf["a"])
            self.assertIs(getattr(conf, "a"), conf["a"], msg="dict/attr consistency")
            self.assertEqual("foo", conf["b"])
            self.assertIs(getattr(conf, "b"), conf["b"], msg="dict/attr consistency")

        def test_getitem_invalid(self):
            conf = self.config_class(a=123)
            with self.assertRaisesRegex(KeyError, "b"):
                _ = conf["b"]

        def test_getitem_invalid_key_type(self):
            conf = self.config_class(a=123)
            with self.assertRaisesRegex(TypeError, "string", msg="int indexing"):
                _ = conf[1]
            with self.assertRaisesRegex(TypeError, "string", msg="obj indexing"):
                _ = conf[object()]
            with self.assertRaisesRegex(TypeError, "string", msg="int-tuple indexing"):
                _ = conf[1, 2, 3]
            with self.assertRaisesRegex(
                TypeError, "string", msg="nested tuple indexing"
            ):
                _ = conf[("a",),]

            with self.assertRaisesRegex(TypeError, "tuple", msg="set indexing"):
                _ = conf[{"a"}]
            with self.assertRaisesRegex(TypeError, "tuple", msg="list indexing"):
                _ = conf[["a"]]

        def test_getitem_class_attributes(self):
            conf = self.config_class()
            with self.assertRaisesRegex(KeyError, "__dict__"):
                _ = conf["__dict__"]
            with self.assertRaisesRegex(KeyError, "__class__"):
                _ = conf["__class__"]
            with self.assertRaisesRegex(KeyError, "items"):
                _ = conf["items"]

        def test_getitem_dotted(self):
            conf = self.config_class(sub=self.config_class(a=123))
            self.assertEqual(123, conf["sub.a"])
            self.assertIs(conf["sub"]["a"], conf["sub.a"], msg="consistency")

        def test_getitem_dotted_invalid(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaisesRegex(KeyError, "b", msg="bad subconfig key"):
                _ = conf["sub.b"]
            with self.assertRaisesRegex(KeyError, "x", msg="bad subconfig"):
                _ = conf["x.b"]

        def test_getitem_tuple(self):
            conf = self.config_class(sub=self.config_class(a=123))
            self.assertEqual(123, conf["sub", "a"])
            self.assertIs(conf["sub"]["a"], conf["sub", "a"], msg="consistency")

        def test_getitem_tuple_empty(self):
            conf = self.config_class(a=123)
            with self.assertRaisesRegex(InvalidKeyError, "empty tuple"):
                _ = conf[()]

        def test_getitem_tuple_invalid(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaisesRegex(KeyError, "b", msg="bad subconfig key"):
                _ = conf["sub", "b"]
            with self.assertRaisesRegex(KeyError, "x", msg="bad subconfig"):
                _ = conf["x", "b"]

        def test_setitem(self):
            conf = self.config_class()
            with self.assertRaises(TypeError):
                conf["a"] = 123

        def test_setitem_overwrite(self):
            conf = self.config_class(a=123)
            with self.assertRaises(TypeError):
                conf["a"] = 234
            self.assertDictEqual({"a": 123}, conf.__dict__)

        def test_setitem_dict(self):
            conf = self.config_class()
            with self.assertRaises(TypeError):
                conf["sub"] = {"a": 123}

        def test_setitem_dict_overwrite(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaises(TypeError):
                conf["sub"] = {"b": "foo"}
            self.assertDictEqual({"sub": FrozenConfiguration(a=123)}, conf.__dict__)

        def test_setitem_invalid_key_type(self):
            conf = self.config_class()
            with self.assertRaises(TypeError, msg="int indexing"):
                conf[1] = 123
            with self.assertRaises(TypeError, msg="obj indexing"):
                conf[object()] = 123
            with self.assertRaises(TypeError, msg="int-tuple indexing"):
                conf[1, 2, 3] = 123

            with self.assertRaises(TypeError, msg="set indexing"):
                conf[{"a"}] = 123
            with self.assertRaises(TypeError, msg="list indexing"):
                conf[["a"]] = [123]

        def test_setitem_class_attributes(self):
            conf = self.config_class()
            with self.assertRaises(TypeError):
                conf["__dict__"] = 123
            with self.assertRaises(TypeError):
                conf["__class__"] = 123
            with self.assertRaises(TypeError):
                del conf["items"]

        def test_setitem_dotted(self):
            conf = self.config_class(sub=self.config_class())
            with self.assertRaises(TypeError):
                conf["sub.a"] = 123

        def test_setitem_dotted_overwrite(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaises(TypeError):
                conf["sub.a"] = 234
            self.assertDictEqual({"sub": self.config_class(a=123)}, conf.__dict__)

        def test_setitem_dotted_create_subconfig(self):
            conf = self.config_class()
            with self.assertRaises(TypeError):
                conf["sub.a"] = 123

        def test_setitem_tuple(self):
            conf = self.config_class(sub=self.config_class())
            with self.assertRaises(TypeError):
                conf["sub", "a"] = 123

        def test_setitem_tuple_empty(self):
            conf = self.config_class()
            with self.assertRaises(TypeError):
                conf[()] = 123

        def test_setitem_tuple_overwrite(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaises(TypeError):
                conf["sub", "a"] = 234
            self.assertDictEqual({"sub": self.config_class(a=123)}, conf.__dict__)

        def test_setitem_tuple_create_subconfig(self):
            conf = self.config_class()
            with self.assertRaises(TypeError):
                conf["sub", "a"] = 123

        def test_delitem(self):
            conf = self.config_class(a=123, b="foo")
            with self.assertRaises(TypeError):
                del conf["a"]
            self.assertDictEqual({"a": 123, "b": "foo"}, conf.__dict__)

        def test_delitem_invalid(self):
            conf = self.config_class(a=123)
            with self.assertRaises(TypeError):
                del conf["b"]

        def test_delitem_invalid_key_type(self):
            conf = self.config_class(a=123)
            with self.assertRaises(TypeError, msg="int indexing"):
                _ = conf[1]
            with self.assertRaises(TypeError, msg="obj indexing"):
                _ = conf[object()]
            with self.assertRaises(TypeError, msg="int-tuple indexing"):
                _ = conf[1, 2, 3]
            with self.assertRaisesRegex(
                TypeError, "string", msg="nested tuple indexing"
            ):
                _ = conf[("a",),]

            with self.assertRaises(TypeError, msg="set indexing"):
                _ = conf[{"a"}]
            with self.assertRaises(TypeError, msg="list indexing"):
                _ = conf[["a"]]

        def test_delitem_class_attributes(self):
            conf = self.config_class()
            with self.assertRaises(TypeError):
                del conf["__dict__"]
            with self.assertRaises(TypeError):
                del conf["__class__"]
            with self.assertRaises(TypeError):
                del conf["items"]

        def test_delitem_dotted(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaises(TypeError):
                del conf["sub.a"]
            self.assertDictEqual({"sub": self.config_class(a=123)}, conf.__dict__)

        def test_delitem_dotted_invalid(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaises(TypeError, msg="bad subconfig key"):
                del conf["sub.b"]
            with self.assertRaises(TypeError, msg="bad subconfig"):
                del conf["x.b"]

        def test_delitem_tuple(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaises(TypeError):
                del conf["sub", "a"]
            self.assertDictEqual({"sub": self.config_class(a=123)}, conf.__dict__)

        def test_delitem_tuple_empty(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaises(TypeError):
                del conf[()]
            self.assertDictEqual({"sub": self.config_class(a=123)}, conf.__dict__)

        def test_delitem_tuple_invalid(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaises(TypeError, msg="bad subconfig key"):
                del conf["sub", "b"]
            with self.assertRaises(TypeError, msg="bad subconfig"):
                del conf["x", "b"]

        def test_iter(self):
            conf = self.config_class(a=123, sub=self.config_class(b="foo", c=None))
            conf_iter = iter(conf)
            self.assertEqual("a", next(conf_iter))
            self.assertEqual("sub", next(conf_iter))
            with self.assertRaises(StopIteration):
                next(conf_iter)

            conf = self.config_class(sub=self.config_class(b="foo", c=None), a=123)
            conf_iter = iter(conf)
            self.assertEqual("sub", next(conf_iter))
            self.assertEqual("a", next(conf_iter))
            with self.assertRaises(StopIteration):
                next(conf_iter)

        def test_update_subconfig(self):
            conf = self.config_class(sub=self.config_class(a=123))
            with self.assertRaisesRegex(AttributeError, "update"):
                conf.update(sub=self.config_class(b="foo"))
            self.assertDictEqual({"sub": self.config_class(a=123)}, conf.__dict__)

        def test_length(self):
            self.assertEqual(0, len(self.config_class()))
            self.assertEqual(1, len(self.config_class(a=123)))
            self.assertEqual(
                2,
                len(self.config_class(a=123, sub=self.config_class(b="foo", c=None))),
            )

        # # # Flat Iterators # # #

        def test_keys(self):
            conf = self.config_class(a=123, b="foo")
            keys = conf.keys()
            self.assertEqual(2, len(keys), msg="has length")
            self.assertIn("a", keys, msg="consistent container")
            self.assertIn("b", keys, msg="consistent container")
            self.assertNotIn("c", keys, msg="consistent container")
            self.assertSequenceEqual(["a", "b"], tuple(keys))

        def test_keys_subconfig(self):
            conf = self.config_class(sub=self.config_class(a=123, b="foo"))
            keys = conf.keys()
            self.assertEqual(1, len(keys), msg="has length")
            self.assertIn("sub", keys, msg="consistent container")
            self.assertNotIn("sub.a", keys, msg="consistent container")
            self.assertNotIn("sub.b", keys, msg="consistent container")
            self.assertSequenceEqual(["sub"], tuple(keys))

        def test_keys_flat(self):
            conf = self.config_class(a=123, b="foo")
            keys = conf.keys(flat=True)
            self.assertEqual(2, len(keys), msg="has length")
            self.assertIn("a", keys, msg="consistent container")
            self.assertIn("b", keys, msg="consistent container")
            self.assertNotIn("c", keys, msg="consistent container")
            self.assertSequenceEqual(["a", "b"], tuple(keys))

        def test_keys_flat_subconfig(self):
            conf = self.config_class(a=123, sub=self.config_class(b="foo", c=None))
            keys = conf.keys(flat=True)
            self.assertIn("a", keys, msg="consistent container")
            self.assertIn("sub.b", keys, msg="consistent container")
            self.assertIn("sub.c", keys, msg="consistent container")
            self.assertNotIn("sub", keys, msg="consistent container")
            self.assertSequenceEqual(["a", "sub.b", "sub.c"], tuple(keys))

        def test_keys_flat_subconfig_empty(self):
            conf = self.config_class(a=123, sub=self.config_class())
            keys = conf.keys(flat=True)
            self.assertSequenceEqual(["a"], tuple(keys))

        def test_items(self):
            conf = self.config_class(a=123, b="foo")
            items = conf.items()
            self.assertEqual(2, len(items), msg="has length")
            self.assertIn(("a", 123), items, msg="consistent container")
            self.assertIn(("b", "foo"), items, msg="consistent container")
            self.assertNotIn(("a", 234), items, msg="consistent container")
            self.assertNotIn(("b", 123), items, msg="consistent container")
            self.assertSequenceEqual([("a", 123), ("b", "foo")], tuple(items))

        def test_items_subconfig(self):
            conf = self.config_class(sub=self.config_class(a=123, b="foo"))
            items = conf.items()
            self.assertEqual(1, len(items), msg="has length")
            self.assertIn(
                ("sub", self.config_class(a=123, b="foo")),
                items,
                msg="consistent container",
            )
            self.assertNotIn(("sub.a", 123), items, msg="consistent container")
            self.assertNotIn(("sub.b", "foo"), items, msg="consistent container")
            self.assertSequenceEqual(
                [("sub", self.config_class(a=123, b="foo"))], tuple(items)
            )

        def test_items_flat(self):
            conf = self.config_class(a=123, b="foo")
            items = conf.items(flat=True)
            self.assertEqual(2, len(items), msg="has length")
            self.assertIn(("a", 123), items, msg="consistent container")
            self.assertIn(("b", "foo"), items, msg="consistent container")
            self.assertNotIn(("a", 234), items, msg="consistent container")
            self.assertNotIn(("b", 123), items, msg="consistent container")
            self.assertSequenceEqual([("a", 123), ("b", "foo")], tuple(items))

        def test_items_flat_subconfig(self):
            conf = self.config_class(a=123, sub=self.config_class(b="foo", c=None))
            items = conf.items(flat=True)
            self.assertIn(("a", 123), items, msg="consistent container")
            self.assertIn(("sub.b", "foo"), items, msg="consistent container")
            self.assertIn(("sub.c", None), items, msg="consistent container")
            self.assertNotIn(
                ("sub", self.config_class(b="foo", c=None)),
                items,
                msg="consistent container",
            )
            self.assertSequenceEqual(
                [("a", 123), ("sub.b", "foo"), ("sub.c", None)], tuple(items)
            )

        def test_items_flat_subconfig_empty(self):
            conf = self.config_class(a=123, sub=self.config_class())
            items = conf.items(flat=True)
            self.assertSequenceEqual([("a", 123)], tuple(items))

        def test_values(self):
            conf = self.config_class(a=123, b="foo")
            values = conf.values()
            self.assertEqual(2, len(values), msg="has length")
            self.assertIn(123, values, msg="consistent container")
            self.assertIn("foo", values, msg="consistent container")
            self.assertNotIn(None, values, msg="consistent container")
            self.assertSequenceEqual([123, "foo"], tuple(values))

        def test_values_subconfig(self):
            conf = self.config_class(sub=self.config_class(a=123, b="foo"))
            values = conf.values()
            self.assertEqual(1, len(values), msg="has length")
            self.assertIn(
                self.config_class(a=123, b="foo"), values, msg="consistent container"
            )
            self.assertNotIn(123, values, msg="consistent container")
            self.assertNotIn("foo", values, msg="consistent container")
            self.assertSequenceEqual([self.config_class(a=123, b="foo")], tuple(values))

        def test_values_flat(self):
            conf = self.config_class(a=123, b="foo")
            values = conf.values(flat=True)
            self.assertEqual(2, len(values), msg="has length")
            self.assertIn(123, values, msg="consistent container")
            self.assertIn("foo", values, msg="consistent container")
            self.assertNotIn(234, values, msg="consistent container")
            self.assertSequenceEqual([123, "foo"], tuple(values))

        def test_values_flat_subconfig(self):
            conf = self.config_class(a=123, sub=self.config_class(b="foo", c=None))
            values = conf.values(flat=True)
            self.assertIn(123, values, msg="consistent container")
            self.assertIn("foo", values, msg="consistent container")
            self.assertIn(None, values, msg="consistent container")
            self.assertNotIn(
                self.config_class(b="foo", c=None), values, msg="consistent container"
            )
            self.assertSequenceEqual([123, "foo", None], tuple(values))

        def test_values_flat_subconfig_empty(self):
            conf = self.config_class(a=123, sub=self.config_class())
            values = conf.values(flat=True)
            self.assertSequenceEqual([123], tuple(values))

        # # # Merging # # #

        def test_union(self):
            conf1 = self.config_class(a=123)
            conf2 = self.config_class(b="foo")
            self.assertEqual(self.config_class(a=123, b="foo"), conf1 | conf2)
            self.assertEqual(
                self.config_class(a=123, b="foo"), conf2 | conf1, msg="symmetry"
            )
            self.assertIsNot(conf1 | conf2, conf1, msg="new object")
            self.assertIsNot(conf1 | conf2, conf2, msg="new object")

        def test_union_empty(self):
            conf = self.config_class(a=123)
            self.assertEqual(conf, conf | self.config_class())
            self.assertEqual(conf, self.config_class() | conf, msg="symmetry")
            self.assertIsNot(conf | self.config_class(), conf, msg="new object")

        def test_union_overlap(self):
            conf1 = self.config_class(a=123, b="foo")
            conf2 = self.config_class(b="bar", c=None)
            self.assertEqual(self.config_class(a=123, b="bar", c=None), conf1 | conf2)
            self.assertEqual(self.config_class(a=123, b="foo", c=None), conf2 | conf1)

        def test_union_overwrite_int(self):
            conf1 = self.config_class(a=123)
            conf2 = self.config_class(a=234)
            self.assertEqual(self.config_class(a=234), conf1 | conf2)
            self.assertEqual(self.config_class(a=123), conf2 | conf1, msg="symmetry")
            self.assertIsNot(conf1 | conf2, conf1, msg="new object")
            self.assertIsNot(conf1 | conf2, conf2, msg="new object")

        def test_union_subconfig(self):
            conf1 = self.config_class(sub=self.config_class(a=123))
            conf2 = self.config_class(sub=self.config_class(b="foo"))
            self.assertEqual(
                self.config_class(sub=self.config_class(a=123, b="foo")),
                conf1 | conf2,
            )
            self.assertEqual(
                self.config_class(sub=self.config_class(a=123, b="foo")),
                conf2 | conf1,
                msg="symmetry",
            )
            self.assertIsNot((conf1 | conf2)["sub"], conf1["sub"], msg="new subconfig")
            self.assertIsNot((conf1 | conf2)["sub"], conf2["sub"], msg="new subconfig")

        def test_union_subconfig_value(self):
            conf1 = self.config_class(sub=123)
            conf2 = self.config_class(sub=self.config_class(b="foo"))
            self.assertEqual(
                self.config_class(sub=self.config_class(b="foo")), conf1 | conf2
            )
            self.assertEqual(
                self.config_class(sub=123),
                conf2 | conf1,
                msg="symmetry",
            )

        def test_union_inplace(self):
            conf = self.config_class(a=123)
            conf |= self.config_class(b="foo")
            self.assertEqual(self.config_class(a=123, b="foo"), conf)

        def test_union_inplace_empty(self):
            conf = self.config_class(a=123)
            conf |= self.config_class()
            self.assertEqual(self.config_class(a=123), conf)

        def test_union_inplace_overlap(self):
            conf = self.config_class(a=123, b="foo")
            conf |= self.config_class(b="bar", c=None)
            self.assertEqual(self.config_class(a=123, b="bar", c=None), conf)

        def test_union_inplace_overwrite_int(self):
            conf = self.config_class(a=123)
            conf |= self.config_class(a=234)
            self.assertEqual(self.config_class(a=234), conf)

        def test_union_inplace_subconfig(self):
            conf = self.config_class(sub=self.config_class(a=123))
            conf |= self.config_class(sub=self.config_class(b="foo"))
            self.assertEqual(
                self.config_class(sub=self.config_class(a=123, b="foo")), conf
            )

        def test_union_inplace_subconfig_value(self):
            conf = self.config_class(sub=123)
            conf |= self.config_class(sub=self.config_class(b="foo"))
            self.assertEqual(self.config_class(sub=self.config_class(b="foo")), conf)

            conf |= self.config_class(sub=123)
            self.assertEqual(self.config_class(sub=123), conf)

        def test_union_dict(self):
            conf = self.config_class(a=123)
            d = {"b": "foo"}
            self.assertEqual(self.config_class(a=123, b="foo"), conf | d)
            self.assertEqual(
                self.config_class(a=123, b="foo"), d | conf, msg="symmetry"
            )
            self.assertIsNot(conf | d, conf, msg="new object")

        def test_union_dict_empty(self):
            conf = self.config_class(a=123)
            self.assertEqual(conf, conf | {})
            self.assertEqual(conf, {} | conf, msg="symmetry")
            self.assertIsNot(conf | {}, conf, msg="new object")

        def test_union_dict_overlap(self):
            conf = self.config_class(a=123, b="foo")
            d = {"b": "bar", "c": None}
            self.assertEqual(self.config_class(a=123, b="bar", c=None), conf | d)
            self.assertEqual(self.config_class(a=123, b="foo", c=None), d | conf)

        def test_union_dict_overwrite_int(self):
            conf1 = self.config_class(a=123)
            d = {"a": 234}
            self.assertEqual(self.config_class(a=234), conf1 | d)
            self.assertEqual(self.config_class(a=123), d | conf1, msg="symmetry")

        def test_union_dict_subconfig(self):
            conf = self.config_class(sub=self.config_class(a=123))
            d = {"sub": {"b": "foo"}}
            self.assertEqual(
                self.config_class(sub=self.config_class(a=123, b="foo")), conf | d
            )
            self.assertEqual(
                self.config_class(sub=self.config_class(a=123, b="foo")),
                d | conf,
                msg="symmetry",
            )

        def test_union_dict_subconfig_value(self):
            conf = self.config_class(sub=123)
            d = {"sub": {"b": "foo"}}
            self.assertEqual(
                self.config_class(sub=self.config_class(b="foo")), conf | d
            )
            self.assertEqual(
                self.config_class(sub=123),
                d | conf,
                msg="symmetry",
            )

        def test_union_dict_dotted_subconfig(self):
            conf = self.config_class(sub=self.config_class(a=123))
            d = {"sub.b": "foo"}
            self.assertEqual(
                self.config_class(sub=self.config_class(a=123, b="foo")), conf | d
            )
            self.assertEqual(
                self.config_class(sub=self.config_class(a=123, b="foo")),
                d | conf,
                msg="symmetry",
            )

        def test_union_dict_dotted_subconfig_value(self):
            conf = self.config_class(sub=123)
            d = {"sub.b": "foo"}
            self.assertEqual(
                self.config_class(sub=self.config_class(b="foo")), conf | d
            )
            self.assertEqual(
                self.config_class(sub=123),
                d | conf,
                msg="symmetry",
            )

        def test_union_dict_dotted_create_subconfig(self):
            conf = self.config_class()
            d = {"sub.b": "foo"}
            self.assertEqual(
                self.config_class(sub=self.config_class(b="foo")), conf | d
            )
            self.assertEqual(
                self.config_class(sub=self.config_class(b="foo")),
                d | conf,
                msg="symmetry",
            )

        # # # Conversions # # #

        def test_from_dict(self):
            conf = self.config_class.from_dict({"a": 123, "b": "foo"})
            self.assertEqual(self.config_class(a=123, b="foo"), conf)
            self.assertIsInstance(conf, self.config_class)

        def test_from_dict_empty(self):
            conf = self.config_class.from_dict({})
            self.assertEqual(self.config_class(), conf)
            self.assertIsInstance(conf, self.config_class)

        def test_from_dict_subconfig(self):
            conf = self.config_class.from_dict({"sub": {"a": 123}})
            self.assertEqual(self.config_class(sub=self.config_class(a=123)), conf)
            self.assertIsInstance(conf, self.config_class)
            self.assertIsInstance(conf.sub, self.config_class)

        def test_from_dict_key_modifiers(self):
            conf = self.config_class.from_dict({"a": 123}, key_mods={"a": "c"})
            self.assertEqual(self.config_class(c=123), conf)

        def test_from_dict_subconfig_key_modifiers(self):
            conf = self.config_class.from_dict({"sub": {"a": 123}}, key_mods={"a": "c"})
            self.assertEqual(self.config_class(sub=self.config_class(c=123)), conf)

        def test_from_dict_subconfig_key_modifiers_shared_pattern(self):
            conf = self.config_class.from_dict({"sub": {"u": 123}}, key_mods={"u": "a"})
            self.assertEqual(self.config_class(sab=self.config_class(a=123)), conf)

        def test_from_dict_key_modifiers_from_dots(self):
            conf = self.config_class.from_dict({"sub.a": 123}, key_mods={".": "_"})
            self.assertEqual(self.config_class(sub_a=123), conf)

        def test_from_dict_key_modifiers_to_dots(self):
            conf = self.config_class.from_dict({"sub_a": 123}, key_mods={"_": "."})
            self.assertEqual(self.config_class(sub=self.config_class(a=123)), conf)

        def test_from_dict_multiple_key_modifiers(self):
            conf = self.config_class.from_dict(
                {"a key": 123}, key_mods={"a": "c", " ": "_"}
            )
            self.assertEqual(self.config_class(c_key=123), conf)

        def test_from_dict_multiple_key_modifiers_overlap(self):
            conf = self.config_class.from_dict(
                {"key": 123}, key_mods={"key": "k", "e": "3"}
            )
            self.assertEqual(self.config_class(k=123), conf)
            conf = self.config_class.from_dict(
                {"key": 123}, key_mods={"e": "3", "key": "k"}
            )
            self.assertEqual(self.config_class(k=123), conf)

        def test_from_dict_chain_key_modifiers(self):
            conf = self.config_class.from_dict(
                {"key": 123}, key_mods={"e": "3", "3": "a"}
            )
            self.assertEqual(self.config_class(k3y=123), conf)

        def test_to_dict(self):
            conf = self.config_class(a=123, b="foo")
            self.assertDictEqual({"a": 123, "b": "foo"}, conf.to_dict())

        def test_to_dict_empty(self):
            conf = self.config_class()
            self.assertDictEqual({}, conf.to_dict())

        def test_to_dict_subconfig(self):
            conf = self.config_class(sub=self.config_class(a=123))
            self.assertDictEqual({"sub": {"a": 123}}, conf.to_dict())
            self.assertIsInstance(conf.to_dict()["sub"], dict)

        def test_to_dict_flat(self):
            conf = self.config_class(sub=self.config_class(a=123, b="foo"))
            self.assertDictEqual(
                {"sub.a": 123, "sub.b": "foo"}, conf.to_dict(flat=True)
            )

        def test_to_dict_key_modifiers(self):
            conf = self.config_class(c=123)
            self.assertDictEqual({"a": 123}, conf.to_dict(key_mods={"c": "a"}))

        def test_to_dict_subconfig_key_modifiers(self):
            conf = self.config_class(sub=self.config_class(c=123))
            self.assertDictEqual({"sub": {"a": 123}}, conf.to_dict(key_mods={"c": "a"}))

        def test_to_dict_subconfig_key_modifiers_shared_pattern(self):
            conf = self.config_class(sab=self.config_class(a=123))
            self.assertDictEqual({"sub": {"u": 123}}, conf.to_dict(key_mods={"a": "u"}))

        def test_to_dict_multiple_key_modifiers(self):
            conf = self.config_class(c_key=123)
            self.assertDictEqual(
                {"a key": 123}, conf.to_dict(key_mods={"c": "a", "_": " "})
            )

        def test_to_dict_multiple_key_modifiers_overlap(self):
            conf = self.config_class(key=123)
            self.assertDictEqual(
                {"k": 123}, conf.to_dict(key_mods={"key": "k", "e": "3"})
            )
            conf = self.config_class(key=123)
            self.assertDictEqual(
                {"k": 123}, conf.to_dict(key_mods={"e": "3", "key": "k"})
            )

        def test_to_dict_chain_key_modifiers(self):
            conf = self.config_class(k3y=123)
            self.assertDictEqual(
                {"key": 123}, conf.to_dict(key_mods={"3": "e", "e": "a"})
            )

        def test_to_dict_flat_key_modifiers_from_dots(self):
            conf = self.config_class(sub=self.config_class(a=123))
            self.assertDictEqual(
                {"sub_a": 123}, conf.to_dict(key_mods={".": "_"}, flat=True)
            )

        # # # Class Attribute Robustness # # #

        def test_repr_robustness(self):
            conf = self.config_class()
            for key in dir(conf):
                conf = self.config_class(**{key: None})
                self.assertEqual(
                    f"{conf.__class__.__name__}({key}=None)",
                    repr(conf),
                    msg=f"overwritten {key}",
                )

        def test_str_robustness(self):
            conf = self.config_class()
            for key in dir(conf):
                conf = self.config_class(**{key: None})
                self.assertEqual(
                    f"{{{key}: None}}", str(conf), msg=f"overwritten {key}"
                )


class TestPlainConfiguration(Utils.TestConfigurationBase):
    @property
    def config_class(self):
        return PlainConfiguration

    # # # Attribute Interface # # #

    def test_setattr(self):
        conf = PlainConfiguration()
        setattr(conf, "a", 123)
        setattr(conf, "b", "foo")
        self.assertDictEqual({"a": 123, "b": "foo"}, conf.__dict__)

    def test_setattr_overwrite(self):
        conf = PlainConfiguration(a=123)
        setattr(conf, "a", 234)
        self.assertDictEqual({"a": 234}, conf.__dict__)

    def test_setattr_dict(self):
        conf = PlainConfiguration()
        setattr(conf, "sub", {"a": 123})
        self.assertDictEqual({"sub": PlainConfiguration(a=123)}, conf.__dict__)
        self.assertIsInstance(conf["sub"], PlainConfiguration)

    def test_setattr_dict_overwrite(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        setattr(conf, "sub", {"b": "foo"})
        self.assertDictEqual({"sub": PlainConfiguration(b="foo")}, conf.__dict__)
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

    def test_setattr_class_attributes(self):
        conf = PlainConfiguration()
        with self.assertRaises(TypeError):
            setattr(conf, "__dict__", 123)
        with self.assertRaises(TypeError):
            setattr(conf, "__class__", 123)

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
        conf = PlainConfiguration(a=123, b="foo")
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
        conf = PlainConfiguration(a=123)
        delattr(conf, "__dict__")
        self.assertDictEqual({}, conf.__dict__)
        with self.assertRaisesRegex(TypeError, "__class__"):
            delattr(conf, "__class__")
        with self.assertRaisesRegex(AttributeError, "items"):
            delattr(conf, "items")

    def test_delattr_dotted(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=[123]))
        with self.assertRaisesRegex(AttributeError, "dot-string"):
            delattr(conf, "sub.a")

    # # # Mapping Interface # # #

    def test_getitem_invalid_key_type_hacky(self):
        conf = PlainConfiguration()
        conf.__dict__ = {1: None}
        with self.assertRaisesRegex(TypeError, "string", msg="int indexing"):
            _ = conf[1]

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
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
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
        conf["__class__"] = None
        conf["items"] = "foo"
        self.assertDictEqual(
            {"__dict__": 123, "__class__": None, "items": "foo"}, conf.__dict__
        )
        self.assertIsInstance(conf, conf.__class__)

    def test_get_setitem_class_attributes(self):
        conf = PlainConfiguration()
        conf["__dict__"] = 123
        self.assertEqual(123, conf["__dict__"])

    def test_del_setitem_class_attributes(self):
        conf = PlainConfiguration(a=123)
        conf["__dict__"] = "foo"
        self.assertIn("__dict__", conf.__dict__)
        del conf["__dict__"]
        self.assertDictEqual({"a": 123}, conf.__dict__)

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

    def test_setitem_tuple_empty(self):
        conf = self.config_class()
        with self.assertRaisesRegex(InvalidKeyError, "empty tuple"):
            conf[()] = 123

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
        with self.assertRaisesRegex(KeyError, "__class__"):
            del conf["__class__"]
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

    def test_delitem_tuple_empty(self):
        conf = self.config_class()
        with self.assertRaisesRegex(InvalidKeyError, "empty tuple"):
            del conf[()]

    def test_delitem_tuple_invalid(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        with self.assertRaisesRegex(KeyError, "b", msg="bad subconfig key"):
            del conf["sub", "b"]
        with self.assertRaisesRegex(KeyError, "x", msg="bad subconfig"):
            del conf["x", "b"]

    def test_update_subconfig(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        conf.update(sub=PlainConfiguration(b="foo"))
        self.assertEqual(PlainConfiguration(sub=PlainConfiguration(b="foo")), conf)

    # # # Flat Iterators # # #

    def test_keys_sync(self):
        conf = PlainConfiguration(a=123)
        keys = conf.keys()
        self.assertEqual(1, len(keys), msg="baseline")
        conf["b"] = "foo"
        self.assertIn("b", keys, msg="consistent container")
        self.assertEqual(2, len(keys), msg="has length")
        self.assertSequenceEqual(["a", "b"], tuple(keys))

    def test_keys_flat_sync(self):
        conf = PlainConfiguration(a=123)
        keys = conf.keys(flat=True)
        self.assertEqual(1, len(keys), msg="baseline")
        conf["b"] = "foo"
        self.assertSequenceEqual(["a", "b"], tuple(keys))

    def test_keys_flat_subconfig_sync(self):
        conf = PlainConfiguration(a=123, sub=PlainConfiguration(b="foo"))
        keys = conf.keys(flat=True)
        self.assertEqual(2, len(keys), msg="baseline")
        conf["sub"]["c"] = None
        self.assertIn("sub.c", keys, msg="consistent container")
        self.assertSequenceEqual(["a", "sub.b", "sub.c"], tuple(keys))

    def test_items_sync(self):
        conf = PlainConfiguration(a=123)
        items = conf.items()
        self.assertEqual(1, len(items), msg="baseline")
        conf["b"] = "foo"
        self.assertEqual(2, len(items), msg="has length")
        self.assertIn(("b", "foo"), items, msg="consistent container")
        self.assertSequenceEqual([("a", 123), ("b", "foo")], tuple(items))

    def test_items_flat_sync(self):
        conf = PlainConfiguration(a=123)
        items = conf.items(flat=True)
        self.assertEqual(1, len(items), msg="baseline")
        conf["b"] = "foo"
        self.assertIn(("b", "foo"), items, msg="consistent container")
        self.assertSequenceEqual([("a", 123), ("b", "foo")], tuple(items))

    def test_items_flat_subconfig_sync(self):
        conf = PlainConfiguration(a=123, sub=PlainConfiguration(b="foo"))
        items = conf.items(flat=True)
        self.assertEqual(2, len(items), msg="baseline")
        conf["sub"]["c"] = None
        self.assertIn(("sub.c", None), items, msg="consistent container")
        self.assertSequenceEqual(
            [("a", 123), ("sub.b", "foo"), ("sub.c", None)], tuple(items)
        )

    def test_values_sync(self):
        conf = PlainConfiguration(a=123)
        values = conf.values()
        self.assertEqual(1, len(values), msg="baseline")
        conf["b"] = "foo"
        self.assertEqual(2, len(values), msg="has length")
        self.assertIn("foo", values, msg="consistent container")
        self.assertSequenceEqual([123, "foo"], tuple(values))

    def test_values_flat_sync(self):
        conf = PlainConfiguration(a=123)
        values = conf.values(flat=True)
        self.assertEqual(1, len(values), msg="baseline")
        conf["b"] = "foo"
        self.assertIn("foo", values, msg="consistent container")
        self.assertSequenceEqual([123, "foo"], tuple(values))

    def test_values_flat_subconfig_sync(self):
        conf = PlainConfiguration(a=123, sub=PlainConfiguration(b="foo"))
        values = conf.values(flat=True)
        self.assertEqual(2, len(values), msg="baseline")
        conf["sub"]["c"] = None
        self.assertIn(None, values, msg="consistent container")
        self.assertSequenceEqual([123, "foo", None], tuple(values))

    # # # Merging # # #

    def test_union_inplace_subconfig_change(self):
        conf = PlainConfiguration(sub=PlainConfiguration(a=123))
        sub_old = conf["sub"]
        conf |= PlainConfiguration(sub=PlainConfiguration(b="foo"))
        self.assertEqual(
            PlainConfiguration(a=123, b="foo"), sub_old, msg="hierarchical"
        )


class TestFrozenConfiguration(Utils.TestConfigurationBase):
    @property
    def config_class(self):
        return FrozenConfiguration

    def test_constructor_sequences(self):
        conf = FrozenConfiguration(a=(123,))
        self.assertDictEqual({"a": (123,)}, conf.__dict__)
        conf = FrozenConfiguration(a=[123])
        self.assertDictEqual({"a": (123,)}, conf.__dict__, msg="list conversion")
        conf = FrozenConfiguration(a={123})
        self.assertDictEqual({"a": (123,)}, conf.__dict__, msg="set conversion")

    def test_constructor_unhashable(self):
        with self.assertRaisesRegex(TypeError, "unhashable"):
            FrozenConfiguration(unhashable=slice(None))

    def test_constructor_unhashable_sequence(self):
        with self.assertRaisesRegex(TypeError, "unhashable"):
            FrozenConfiguration(unhashable=[slice(None)])

    # # # Immutability (consenting adults) # # #
    #
    # def test_constructor_reuse(self):
    #     conf = FrozenConfiguration(a=123)
    #     conf.__init__(b="foo")
    #     self.assertDictEqual({"a": 123}, conf.__dict__)
    #
    # def test_dict_manipulation(self):
    #     conf = FrozenConfiguration(a=123)
    #     conf.__dict__["b"] = "foo"
    #     self.assertDictEqual({"a": 123}, conf.__dict__)

    # # # Hashing # # #

    def test_hash(self):
        conf = FrozenConfiguration(a=123, b=None)
        self.assertEqual(hash(conf), hash(FrozenConfiguration(a=123, b=None)))
        self.assertEqual(hash(conf), hash(conf), msg="identity")
        self.assertEqual(
            hash(conf), hash(FrozenConfiguration(b=None, a=123)), msg="ordering"
        )
        self.assertNotEqual(
            hash(conf), hash(FrozenConfiguration(a=123)), msg="cardinality"
        )
        self.assertNotEqual(
            hash(conf), hash(FrozenConfiguration(ax=123, bx=None)), msg="respect key"
        )
        self.assertNotEqual(
            hash(conf), hash(FrozenConfiguration(a=234, b=None)), msg="respect value"
        )
        self.assertNotEqual(
            hash(conf),
            hash(FrozenConfiguration(a=None, b=123)),
            msg="respect key-value",
        )

    def test_hash_hierarchical(self):
        conf = FrozenConfiguration(sub=FrozenConfiguration(a=123))
        self.assertEqual(hash(conf), hash(conf), msg="identity")
        self.assertEqual(
            hash(conf),
            hash(FrozenConfiguration(sub=FrozenConfiguration(a=123))),
        )
        self.assertNotEqual(
            hash(conf),
            hash(FrozenConfiguration(sub=FrozenConfiguration(a=234))),
            msg="respect value",
        )
        self.assertNotEqual(
            hash(conf),
            hash(FrozenConfiguration(other=FrozenConfiguration(a=123))),
            msg="respect key",
        )

    def test_hash_collision_values(self):
        count = 1024
        unique_int = {hash(FrozenConfiguration(a=2023 + i)) for i in range(count)}
        self.assertEqual(count, len(unique_int), msg="int values")
        unique_str = {
            hash(FrozenConfiguration(a=f"value{i:02d}")) for i in range(count)
        }
        self.assertEqual(count, len(unique_str), msg="str values")

    def test_hash_collision_keys(self):
        keys = tuple(enumerate("abcdefghi"))
        uniques = {
            hash(FrozenConfiguration(**{k: 123 for b, k in keys if (1 << b) & i}))
            for i in range(1 << len(keys))
        }
        self.assertEqual(1 << len(keys), len(uniques))

    def test_hash_collision_items(self):
        items = tuple(zip("abcdefghi", range(9)))
        uniques = {
            hash(FrozenConfiguration(**{k: v + 1 for k, v in items if (1 << v) & i}))
            for i in range(1 << len(items))
        }
        self.assertEqual(1 << len(items), len(uniques))

    def test_hash_collision_recursions(self):
        uniques, conf, depth = set(), {}, 21
        for _ in range(depth):
            conf = FrozenConfiguration(sub=conf)
            uniques.add(hash(conf))

        self.assertEqual(depth, len(uniques))

    # # # Attribute Interface # # #

    def test_setattr(self):
        conf = FrozenConfiguration()
        with self.assertRaisesRegex(AttributeError, "no attribute 'a'"):
            setattr(conf, "a", 123)

    def test_setattr_overwrite(self):
        conf = FrozenConfiguration(a=123)
        with self.assertRaisesRegex(AttributeError, "'a' is read-only"):
            setattr(conf, "a", 234)
        self.assertDictEqual({"a": 123}, conf.__dict__)

    def test_setattr_dict(self):
        conf = FrozenConfiguration()
        with self.assertRaisesRegex(AttributeError, "no attribute 'sub'"):
            setattr(conf, "sub", {"a": 123})

    def test_setattr_dict_overwrite(self):
        conf = FrozenConfiguration(sub=FrozenConfiguration(a=123))
        with self.assertRaisesRegex(AttributeError, "'sub' is read-only"):
            setattr(conf, "sub", {"a": 234})
        self.assertDictEqual({"sub": FrozenConfiguration(a=123)}, conf.__dict__)

    def test_setattr_invalid_key_type(self):
        conf = FrozenConfiguration()
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

    def test_setattr_class_attributes(self):
        conf = FrozenConfiguration()
        with self.assertRaisesRegex(AttributeError, "'__dict__'"):
            setattr(conf, "__dict__", 123)
        with self.assertRaisesRegex(AttributeError, "'__class__'"):
            setattr(conf, "__class__", 123)
        with self.assertRaisesRegex(AttributeError, "'items' is read-only"):
            setattr(conf, "items", "foo")

    def test_setattr_dotted(self):
        conf = FrozenConfiguration(sub=FrozenConfiguration())
        with self.assertRaisesRegex(AttributeError, "dot-string"):
            setattr(conf, "sub.a", 123)
        self.assertDictEqual({"sub": FrozenConfiguration()}, conf.__dict__)

    def test_delattr(self):
        conf = FrozenConfiguration(a=123, b="foo")
        with self.assertRaisesRegex(AttributeError, "'a' is read-only"):
            delattr(conf, "a")
        self.assertDictEqual({"a": 123, "b": "foo"}, conf.__dict__)

    def test_delatrr_invalid(self):
        conf = FrozenConfiguration(a=123)
        with self.assertRaisesRegex(AttributeError, "b"):
            delattr(conf, "b")

    def test_delattr_invalid_key_type(self):
        conf = FrozenConfiguration(a=123)
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
        conf = FrozenConfiguration(a=123)
        with self.assertRaisesRegex(AttributeError, "__dict__"):
            delattr(conf, "__dict__")
        self.assertDictEqual({"a": 123}, conf.__dict__)
        with self.assertRaisesRegex(AttributeError, "__class__"):
            delattr(conf, "__class__")
        self.assertIsInstance(conf, conf.__class__)
        with self.assertRaisesRegex(AttributeError, "items"):
            delattr(conf, "items")

    def test_delattr_dotted(self):
        conf = FrozenConfiguration(sub=FrozenConfiguration(a=123))
        with self.assertRaisesRegex(AttributeError, "dot-string"):
            delattr(conf, "sub.a")
        self.assertDictEqual({"sub": FrozenConfiguration(a=123)}, conf.__dict__)

    # # # Merging # # #

    def test_union_inplace_subconfig_change(self):
        super().test_union_inplace_subconfig()
        old_conf = conf = FrozenConfiguration(sub=FrozenConfiguration(a=123))
        sub_old = conf["sub"]
        conf |= FrozenConfiguration(sub=FrozenConfiguration(b="foo"))
        self.assertIsNot(old_conf, conf)
        self.assertEqual(FrozenConfiguration(a=123), sub_old, msg="hierarchical")
