# coding=utf8

'''Test .NET autoapi objects'''

import os
import unittest
from collections import namedtuple

from jinja2 import Environment, FileSystemLoader

from autoapi.mappers import dotnet
from autoapi.mappers import python
from autoapi.settings import TEMPLATE_DIR


class DotNetObjectTests(unittest.TestCase):

    def test_type(self):
        '''Test types of some of the objects'''
        obj = dotnet.DotNetNamespace({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'namespace')
        self.assertEqual(obj.ref_type, 'namespace')
        self.assertEqual(obj.ref_directive, 'ns')

        obj = dotnet.DotNetMethod({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'method')
        self.assertEqual(obj.ref_type, 'method')
        self.assertEqual(obj.ref_directive, 'meth')

        obj = dotnet.DotNetProperty({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'property')
        self.assertEqual(obj.ref_type, 'property')
        self.assertEqual(obj.ref_directive, 'prop')

        obj = dotnet.DotNetEnum({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'enum')
        self.assertEqual(obj.ref_type, 'enumeration')
        self.assertEqual(obj.ref_directive, 'enum')

        obj = dotnet.DotNetStruct({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'struct')
        self.assertEqual(obj.ref_type, 'structure')
        self.assertEqual(obj.ref_directive, 'struct')

        obj = dotnet.DotNetConstructor({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'constructor')
        self.assertEqual(obj.ref_type, 'constructor')
        self.assertEqual(obj.ref_directive, 'ctor')

        obj = dotnet.DotNetInterface({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'interface')
        self.assertEqual(obj.ref_type, 'interface')
        self.assertEqual(obj.ref_directive, 'iface')

        obj = dotnet.DotNetDelegate({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'delegate')
        self.assertEqual(obj.ref_type, 'delegate')
        self.assertEqual(obj.ref_directive, 'del')

        obj = dotnet.DotNetClass({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'class')
        self.assertEqual(obj.ref_type, 'class')
        self.assertEqual(obj.ref_directive, 'cls')

        obj = dotnet.DotNetField({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'field')
        self.assertEqual(obj.ref_type, 'field')
        self.assertEqual(obj.ref_directive, 'field')

        obj = dotnet.DotNetEvent({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'event')
        self.assertEqual(obj.ref_type, 'event')
        self.assertEqual(obj.ref_directive, 'event')

    def test_names(self):
        '''Test names of objects'''
        obj = dotnet.DotNetNamespace({'id': 'Foo.Bar'})
        self.assertEqual(obj.name, 'Foo.Bar')
        self.assertEqual(obj.short_name, 'Bar')

        obj = dotnet.DotNetNamespace({'id': 'Foo.Bar.Something`1'})
        self.assertEqual(obj.name, 'Foo.Bar.Something`1')
        self.assertEqual(obj.short_name, 'Something`1')

    def test_namespace_namespace(self):
        '''Namespace parent resolution'''
        ns = dotnet.DotNetNamespace({'id': 'Foo.Bar.Widgets'})
        self.assertEqual(ns.namespace, 'Foo.Bar')
        ns = dotnet.DotNetNamespace({'id': 'Foo.Bar'})
        self.assertEqual(ns.namespace, 'Foo')
        ns = dotnet.DotNetNamespace({'id': 'Foo'})
        self.assertIsNone(ns.namespace)

    def test_class_namespace(self):
        '''Class parent resolution'''
        cls = dotnet.DotNetClass(dict(id='Foo.Bar.Widget',
                                      type='class'))
        self.assertEqual(cls.namespace, 'Foo.Bar')
        cls = dotnet.DotNetClass(dict(id='Foo.Bar',
                                      type='class'))
        self.assertEqual(cls.namespace, 'Foo')
        cls = dotnet.DotNetClass(dict(id='Foo',
                                      type='class'))
        self.assertIsNone(cls.namespace)

    def test_filename(self):
        '''Object file name'''
        cls = dotnet.DotNetClass({'id': 'Foo.Bar.Widget'})
        self.assertEqual(cls.pathname, os.path.join('Foo', 'Bar', 'Widget'))
        cls = dotnet.DotNetClass({'id': 'Foo.Bar.Widget<T>'})
        self.assertEqual(cls.pathname, os.path.join('Foo', 'Bar', 'Widget-T'))
        cls = dotnet.DotNetClass({'id': 'Foo.Bar.Widget<T>(TFoo)'})
        self.assertEqual(cls.pathname, os.path.join('Foo', 'Bar', 'Widget-T'))
        cls = dotnet.DotNetClass({'id': 'Foo.Foo-Bar.Widget<T>(TFoo)'})
        self.assertEqual(cls.pathname, os.path.join('Foo', 'FooBar', 'Widget-T'))
        cls = dotnet.DotNetClass({'id': u'Foo.Bär'})
        self.assertEqual(cls.pathname, os.path.join('Foo', 'Bar'))
        cls = dotnet.DotNetClass({'id': u'Ащщ.юИфк'})
        self.assertEqual(cls.pathname, os.path.join('Ashchshch', 'iuIfk'))

    def test_rendered_class_escaping(self):
        """Rendered class escaping"""
        jinja_env = Environment(
            loader=FileSystemLoader([TEMPLATE_DIR]),
        )
        cls = dotnet.DotNetClass(
            {
                'id': 'Foo.Bar`1',
                'inheritance': ['Foo.Baz`1'],
            },
            jinja_env=jinja_env)
        self.assertIn('* :dn:cls:`Foo.Baz\\`1`\n', cls.render())

    def test_include_path(self):
        """Include path"""
        cls = dotnet.DotNetClass({'id': 'Foo.Bar.Widget'})
        self.assertEqual(cls.include_path, '/autoapi/Foo/Bar/Widget/index')
        cls = dotnet.DotNetClass({'id': 'Foo.Bar.Widget'}, url_root='/autofoo')
        self.assertEqual(cls.include_path, '/autofoo/Foo/Bar/Widget/index')


class PythonObjectTests(unittest.TestCase):

    def test_full_name(self):
        """Full name resolution on nested objects"""
        Source = namedtuple('Source', ['kind', 'name', 'parent'])

        obj_module = Source(kind='module', name='example/example.py', parent=None)
        obj_class = Source(kind='class', name='Foo', parent=obj_module)
        obj_method = Source(kind='method', name='bar', parent=obj_class)

        self.assertEqual(
            python.PythonPythonMapper._get_full_name(obj_module),
            'example.example'
        )
        self.assertEqual(
            python.PythonPythonMapper._get_full_name(obj_class),
            'example.example.Foo'
        )
        self.assertEqual(
            python.PythonPythonMapper._get_full_name(obj_method),
            'example.example.Foo.bar'
        )

    def test_arguments(self):
        """Argument parsing of source"""
        Source = namedtuple('Source', ['source', 'docstring'])

        obj = Source(
            source=('def foobar(self, bar, baz=42, foo=True,\n'
                    '           *args, **kwargs):\n'
                    '    "This is a docstring"\n'
                    '    return True\n'),
            docstring='"This is a docstring"',
        )

        self.assertEqual(
            python.PythonPythonMapper._get_arguments(obj),
            ['self', 'bar', 'baz=42', 'foo=True', '*args', '**kwargs']
        )

    def test_advanced_arguments(self):
        """Advanced argument parsing"""
        Source = namedtuple('Source', ['source', 'docstring'])

        obj = Source(
            source=('def foobar(self, a, b, c=42, d="string", e=(1,2),\n'
                    '           f={"a": True}, g=None, h=[1,2,3,4],\n'
                    '           i=dict(a=True), j=False, *args, **kwargs):\n'
                    '    "This is a docstring"\n'
                    '    return True\n'),
            docstring='"This is a docstring"',
        )

        self.assertEqual(
            python.PythonPythonMapper._get_arguments(obj),
            [
                'self',
                'a',
                'b',
                'c=42',
                'd="string"',
                'e=tuple',
                'f=dict',
                'g=None',
                'h=list',
                'i=dict',
                'j=False',
                '*args',
                '**kwargs',
            ]
        )

    def test_bunk_whitespace(self):
        """Whitespace in definition throws off argument parsing"""
        Source = namedtuple('Source', ['source', 'docstring'])

        obj = Source(
            source=('    def method_foo(self, a, b,\n'
                    '                   c):\n'
                    '        call_something()\n'
                    '        "This is a docstring"\n'
                    '        return True\n'),
            docstring='"This is a docstring"',
        )
        self.assertEqual(
            python.PythonPythonMapper._get_arguments(obj),
            ['self', 'a', 'b', 'c']
        )
