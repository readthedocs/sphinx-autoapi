# coding=utf8

"""Test Python parser"""

import sys
import unittest
from textwrap import dedent

from autoapi.mappers.python import ParserExtra

if sys.version_info < (3, 0):
    from StringIO import StringIO
else:
    from io import StringIO


class PythonParserTests(unittest.TestCase):

    def parse(self, source):
        in_h = StringIO(dedent(source))
        return ParserExtra()(in_h, '/dev/null')

    def test_parses_basic_file(self):
        source = """
        def foo(bar):
            pass
        """
        self.assertIsNone(self.parse(source).all)

    def test_parses_all(self):
        source = """
        __all__ = ['Foo', 5.0]
        """
        self.assertEqual(self.parse(source).all, ['Foo', 5.0])

    def test_parses_all_with_list_addition(self):
        source = """
        __all__ = ['Foo'] + []
        """
        self.assertEqual(self.parse(source).all, ['Foo'])

    def test_parses_all_with_name_addtion(self):
        source = """
        __all__ = ['Foo'] + bar.__all__
        """
        self.assertEqual(self.parse(source).all, ['Foo'])

    def test_parses_all_with_multiple_name_addtions(self):
        source = """
        __all__ = foo + bar
        __all__ += boop
        __all__ += ['foo']
        """
        self.assertEqual(self.parse(source).all, ['foo'])
        source = """
        __all__ = ['foo']
        __all__ = foo
        """
        self.assertEqual(self.parse(source).all, [])

    def test_parses_all_multiline(self):
        source = """
        __all__ = [
            'foo',
            'bar',
        ]
        """
        self.assertEqual(self.parse(source).all, ['foo', 'bar'])

    def test_parses_all_generator(self):
        source = """
        __all__ = [x for x in dir(token) if x[0] != '_'] + ['foo', 'bar']
        """
        out = self.parse(source)
        self.assertEqual(self.parse(source).all, ['foo', 'bar'])

    def test_parses_name(self):
        source = "foo.bar"
        self.assertEqual(self.parse(source).children, [])

    def test_parses_list(self):
        source = "__all__ = [[1, 2], [3, 4]]"
        self.assertEqual(self.parse(source).all, [[1, 2], [3, 4]])
