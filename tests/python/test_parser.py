# coding=utf8

"""Test Python parser"""

import sys
import unittest
from textwrap import dedent

import astroid
import pytest

from autoapi.mappers.python.parser import Parser

if sys.version_info < (3, 0):
    from StringIO import StringIO
else:
    from io import StringIO


class PythonParserTests(unittest.TestCase):
    def parse(self, source):
        node = astroid.extract_node(source)
        return Parser().parse(node)

    def test_parses_basic_file(self):
        source = """
        def foo(bar):
            pass
        """
        data = self.parse(source)[0]
        self.assertEqual(data["name"], "foo")
        self.assertEqual(data["type"], "function")

    def test_parses_all(self):
        source = """
        __all__ = ['Foo', 5.0]
        """
        data = self.parse(source)[0]
        self.assertEqual(data["name"], "__all__")
        self.assertEqual(data["value"], ["Foo", 5.0])

    def test_parses_all_multiline(self):
        source = """
        __all__ = [
            'foo',
            'bar',
        ]
        """
        data = self.parse(source)[0]
        self.assertEqual(data["value"], ["foo", "bar"])

    def test_parses_name(self):
        source = "foo.bar"
        self.assertEqual(self.parse(source), {})

    def test_parses_list(self):
        name = "__all__"
        value = [1, 2, 3, 4]
        source = "{} = {}".format(name, value)
        data = self.parse(source)[0]
        self.assertEqual(data["name"], name)
        self.assertEqual(data["value"], value)

    def test_parses_nested_list(self):
        name = "__all__"
        value = [[1, 2], [3, 4]]
        source = "{} = {}".format(name, value)
        data = self.parse(source)[0]
        self.assertEqual(data["name"], name)
        self.assertEqual(data["value"], value)

    def test_arguments(self):
        """Argument parsing of source"""
        source = (
            "def foobar(self, bar, baz=42, foo=True,\n"
            "           *args, **kwargs):\n"
            '    "This is a docstring"\n'
            "    return True\n"
        )
        data = self.parse(source)[0]
        self.assertEqual(data["args"], "self, bar, baz=42, foo=True, *args, **kwargs")

    def test_advanced_arguments(self):
        """Advanced argument parsing"""
        source = (
            'def foobar(self, a, b, c=42, d="string", e=(1,2),\n'
            '           f={"a": True}, g=None, h=[1,2,3,4],\n'
            "           i=dict(a=True), j=False, *args, **kwargs):\n"
            '    "This is a docstring"\n'
            "    return True\n"
        )
        data = self.parse(source)[0]
        self.assertEqual(
            data["args"],
            ", ".join(
                [
                    "self",
                    "a",
                    "b",
                    "c=42",
                    "d='string'",
                    "e=(1, 2)",
                    "f={'a': True}",
                    "g=None",
                    "h=[1, 2, 3, 4]",
                    "i=dict(a=True)",
                    "j=False",
                    "*args",
                    "**kwargs",
                ]
            ),
        )

    def test_dict_key_assignment(self):
        """Ignore assignment to dictionary entries."""
        source = """
        MY_DICT = {}  #@
        if condition:
            MY_DICT['key'] = 'value'
        MY_DICT['key2'] = 'value2'
        """
        data = self.parse(source)[0]
        self.assertEqual(data["name"], "MY_DICT")

    def test_list_index_assignment(self):
        """Ignore assignment to indexes."""
        source = """
        COLOUR = [255, 128, 0]  #@
        if condition:
            COLOUR[1] = 255
        COLOUR[2] = 255
        """
        data = self.parse(source)[0]
        self.assertEqual(data["name"], "COLOUR")
