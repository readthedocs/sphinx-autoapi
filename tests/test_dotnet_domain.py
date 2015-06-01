'''Test .NET autoapi domain'''

import unittest
import time
from contextlib import nested

from mock import patch

from autoapi.domains import dotnet


class DomainTests(unittest.TestCase):

    def setUp(self):
        '''Test setup'''
        class _config(object):
            autoapi_dir = '/tmp/autoapi/tmp'
            autoapi_root = '/tmp/autoapi/root'

        class _application(object):
            config = _config()

            def warn(self, *args, **kwargs):
                pass

        self.application = _application()

    def test_config(self):
        '''Sphinx app config'''
        dom = dotnet.DotNetDomain(self.application)
        self.assertEqual(dom.get_config('autoapi_dir'), '/tmp/autoapi/tmp')
        self.assertEqual(dom.get_config('autoapi_dir'), '/tmp/autoapi/tmp')

    def test_create_class(self):
        '''Test .NET class instance creation helper'''
        dom = dotnet.DotNetDomain(self.application)
        def _create_class(data):
            return list(dom.create_class(data))[0]
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Namespace'})
        self.assertIsInstance(cls, dotnet.DotNetNamespace)
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Class'})
        self.assertIsInstance(cls, dotnet.DotNetClass)
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Property'})
        self.assertIsInstance(cls, dotnet.DotNetProperty)
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Method'})
        self.assertIsInstance(cls, dotnet.DotNetMethod)
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Enum'})
        self.assertIsInstance(cls, dotnet.DotNetEnum)
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Constructor'})
        self.assertIsInstance(cls, dotnet.DotNetConstructor)
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Struct'})
        self.assertIsInstance(cls, dotnet.DotNetStruct)
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Interface'})
        self.assertIsInstance(cls, dotnet.DotNetInterface)
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Delegate'})
        self.assertIsInstance(cls, dotnet.DotNetDelegate)
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Field'})
        self.assertIsInstance(cls, dotnet.DotNetField)
        cls = _create_class({'id': 'Foo.Bar', 'type': 'Event'})
        self.assertIsInstance(cls, dotnet.DotNetEvent)

    def test_create_class_with_children(self):
        dom = dotnet.DotNetDomain(self.application)
        def _create_class(data):
            return list(dom.create_class(data))[0]
        cls = _create_class({'id': 'Foo.Bar',
                             'type': 'Class',
                             'items': [
                                 {'id': 'Foo.Bar.Baz',
                                  'type': 'Method'}
                             ]})
        self.assertIsInstance(cls, dotnet.DotNetClass)
        self.assertDictEqual(cls.item_map, {})

    def test_get_objects(self):
        '''Test basic get objects'''
        objs = []

        def _mock_find(self, pattern):
            return {'items': ['foo', 'bar']}

        def _mock_read(self, path):
            return {'items': [{'id': 'Foo.Bar', 'name': 'Foo', 'type': 'property'},
                              {'id': 'Foo.Bar2', 'name': 'Bar', 'type': 'property'}],
                    'id': 'Foo.Bar', 'type': 'Class', 'summary': path}

        def _mock_add(self, obj):
            objs.append(obj)

        def _mock_config(self, key):
            return 'foo'

        with nested(
                patch('autoapi.domains.dotnet.DotNetDomain.find_files', _mock_find),
                patch('autoapi.domains.dotnet.DotNetDomain.read_file', _mock_read),
                patch('autoapi.domains.dotnet.DotNetDomain.get_config', _mock_config),
                ):
            dom = dotnet.DotNetDomain(self.application)
            dom.get_objects('*')
            objs = dom.objects
            self.assertEqual(len(objs), 2)
            self.assertEqual(objs['Foo.Bar'].id, 'Foo.Bar')
            self.assertEqual(objs['Foo.Bar'].name, 'Foo.Bar')
            self.assertEqual(objs['Foo.Bar2'].id, 'Foo.Bar2')
            self.assertEqual(objs['Foo.Bar2'].name, 'Foo.Bar2')
