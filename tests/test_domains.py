'''Test .NET autoapi domain'''

import unittest

from mock import patch

from autoapi.mappers import dotnet


class DomainTests(unittest.TestCase):

    def setUp(self):
        '''Test setup'''
        class _config(object):
            autoapi_dirs = ['/tmp/autoapi/tmp']
            autoapi_root = '/tmp/autoapi/root'

        class _application(object):
            config = _config()

            def warn(self, *args, **kwargs):
                pass

        self.application = _application()

    def test_create_class(self):
        '''Test .NET class instance creation helper'''
        dom = dotnet.DotNetSphinxMapper(self.application)

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
        dom = dotnet.DotNetSphinxMapper(self.application)

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

    @patch('subprocess.check_output', lambda foo: foo)
    def test_get_objects(self):
        '''Test basic get objects'''
        objs = []

        def _mock_find(self, patterns, **kwargs):
            return {'items': ['foo', 'bar']}

        def _mock_read(self, path):
            return {'items': [{'id': 'Foo.Bar', 'name': 'Foo', 'type': 'property'},
                              {'id': 'Foo.Bar2', 'name': 'Bar', 'type': 'property'}],
                    'id': 'Foo.Bar', 'type': 'Class', 'summary': path}

        with patch('autoapi.mappers.dotnet.DotNetSphinxMapper.find_files', _mock_find):
            with patch('autoapi.mappers.dotnet.DotNetSphinxMapper.read_file', _mock_read):
                dom = dotnet.DotNetSphinxMapper(self.application)
                dom.load('', '', '', raise_error=False)
                dom.map()
                objs = dom.objects
                self.assertEqual(len(objs), 2)
                self.assertEqual(objs['Foo.Bar'].id, 'Foo.Bar')
                self.assertEqual(objs['Foo.Bar'].name, 'Foo.Bar')
                self.assertEqual(objs['Foo.Bar2'].id, 'Foo.Bar2')
                self.assertEqual(objs['Foo.Bar2'].name, 'Foo.Bar2')

    def test_xml_parse(self):
        '''XML doc comment parsing'''
        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'This is an example comment <see cref="FOO" />')
        self.assertEqual(ret, 'This is an example comment :any:`FOO`')

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'This is an example comment <see cref="!:FOO" />')
        self.assertEqual(ret, 'This is an example comment FOO')

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'This is an example comment <see cref="N:FOO">inner foo</see>')
        self.assertEqual(ret, 'This is an example comment :dn:ns:`FOO`')

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'Test <see cref="P:FOO" /> and <see cref="E:BAR">Blah</see>')
        self.assertEqual(ret, 'Test :dn:prop:`FOO` and :dn:event:`BAR`')

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'This is an example comment <paramref name="FOO" />')
        self.assertEqual(ret, 'This is an example comment ``FOO``')

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'This is an example comment <typeparamref name="FOO" />')
        self.assertEqual(ret, 'This is an example comment ``FOO``')

    def test_xml_transform_escape(self):
        """XML transform escaping"""
        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'Foo <see cref="Foo`1" /> Bar')
        self.assertEqual(ret, 'Foo :any:`Foo\\`1` Bar')

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'No space before<see cref="M:Foo`1" />or after')
        self.assertEqual(ret, 'No space before :dn:meth:`Foo\\`1`\\or after')
