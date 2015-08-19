# coding=utf8

'''Test .NET autoapi objects'''

import os
import unittest

from autoapi.mappers import dotnet


class NamespaceTests(unittest.TestCase):

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
