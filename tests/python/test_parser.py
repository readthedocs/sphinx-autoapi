# coding=utf8

"""Test Python parser"""

from io import StringIO
import sys
from textwrap import dedent

import astroid
import pytest

from autoapi.mappers.python.parser import Parser


class TestPythonParser:
    def parse(self, source):
        node = astroid.extract_node(source)
        return Parser().parse(node)

    def test_parses_basic_file(self):
        source = """
        def foo(bar):
            pass
        """
        data = self.parse(source)[0]
        assert data["name"] == "foo"
        assert data["type"] == "function"

    def test_parses_all(self):
        source = """
        __all__ = ['Foo', 5.0]
        """
        data = self.parse(source)[0]
        assert data["name"] == "__all__"
        assert data["value"] == ["Foo", 5.0]

    def test_parses_all_multiline(self):
        source = """
        __all__ = [
            'foo',
            'bar',
        ]
        """
        data = self.parse(source)[0]
        assert data["value"] == ["foo", "bar"]

    def test_parses_name(self):
        source = "foo.bar"
        assert self.parse(source) == {}

    def test_parses_list(self):
        name = "__all__"
        value = [1, 2, 3, 4]
        source = "{} = {}".format(name, value)
        data = self.parse(source)[0]
        assert data["name"] == name
        assert data["value"] == value

    def test_parses_nested_list(self):
        name = "__all__"
        value = [[1, 2], [3, 4]]
        source = "{} = {}".format(name, value)
        data = self.parse(source)[0]
        assert data["name"] == name
        assert data["value"] == value

    def test_arguments(self):
        """Argument parsing of source"""
        source = (
            "def foobar(self, bar, baz=42, foo=True,\n"
            "           *args, **kwargs):\n"
            '    "This is a docstring"\n'
            "    return True\n"
        )
        data = self.parse(source)[0]
        expected = [
            (None, "self", None, None),
            (None, "bar", None, None),
            (None, "baz", None, "42"),
            (None, "foo", None, "True"),
            ("*", "args", None, None),
            ("**", "kwargs", None, None),
        ]
        assert data["args"] == expected

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
        expected = [
            (None, "self", None, None),
            (None, "a", None, None),
            (None, "b", None, None),
            (None, "c", None, "42"),
            (None, "d", None, "'string'"),
            (None, "e", None, "(1, 2)"),
            (None, "f", None, "{'a': True}"),
            (None, "g", None, "None"),
            (None, "h", None, "[1, 2, 3, 4]"),
            (None, "i", None, "dict(a=True)"),
            (None, "j", None, "False"),
            ("*", "args", None, None),
            ("**", "kwargs", None, None),
        ]
        assert data["args"] == expected

    def test_dict_key_assignment(self):
        """Ignore assignment to dictionary entries."""
        source = """
        MY_DICT = {}  #@
        if condition:
            MY_DICT['key'] = 'value'
        MY_DICT['key2'] = 'value2'
        """
        data = self.parse(source)[0]
        assert data["name"] == "MY_DICT"

    def test_list_index_assignment(self):
        """Ignore assignment to indexes."""
        source = """
        COLOUR = [255, 128, 0]  #@
        if condition:
            COLOUR[1] = 255
        COLOUR[2] = 255
        """
        data = self.parse(source)[0]
        assert data["name"] == "COLOUR"
