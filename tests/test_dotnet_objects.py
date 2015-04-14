'''Test .NET autoapi objects'''

import unittest
import time

from autoapi.domains import dotnet


class NamespaceTests(unittest.TestCase):

    def test_type(self):
        '''Test types of some of the objects'''
        obj = dotnet.DotNetNamespace({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'namespace')
        self.assertEqual(obj.ref_type, 'ns')

        obj = dotnet.DotNetMethod({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'method')
        self.assertEqual(obj.ref_type, 'meth')

        obj = dotnet.DotNetClass({'id': 'Foo.Bar'})
        self.assertEqual(obj.type, 'class')
        self.assertEqual(obj.ref_type, 'cls')

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
