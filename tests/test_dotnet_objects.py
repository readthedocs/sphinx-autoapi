'''Test .NET autoapi objects'''

import unittest
import time

from autoapi.domains import dotnet


class NamespaceTests(unittest.TestCase):

    def test_namespace_namespace(self):
        '''Namespace parent resolution'''
        ns = dotnet.DotNetNamespace(dict(id='Foo.Bar.Widgets',
                                         type='namespace'))
        self.assertEqual(ns.namespace(), 'Foo.Bar')
        ns = dotnet.DotNetNamespace(dict(id='Foo.Bar',
                                         type='namespace'))
        self.assertEqual(ns.namespace(), 'Foo')
        ns = dotnet.DotNetNamespace(dict(id='Foo',
                                         type='namespace'))
        self.assertIsNone(ns.namespace())

    def test_class_namespace(self):
        '''Class parent resolution'''
        cls = dotnet.DotNetClass(dict(id='Foo.Bar.Widget',
                                      type='class'))
        self.assertEqual(cls.namespace(), 'Foo.Bar')
        cls = dotnet.DotNetClass(dict(id='Foo.Bar',
                                      type='class'))
        self.assertEqual(cls.namespace(), 'Foo')
        cls = dotnet.DotNetClass(dict(id='Foo',
                                      type='class'))
        self.assertIsNone(cls.namespace())
