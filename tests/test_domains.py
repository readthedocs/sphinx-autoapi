"""Test .NET autoapi domain"""

from unittest import mock
from unittest.mock import patch

from autoapi.mappers import dotnet


class MockConfig:
    def __getattr__(self, key):
        attrs = {
            "autoapi_dirs": ["/tmp/autoapi/tmp"],
            "autoapi_root": "/tmp/autoapi/root",
        }
        return attrs.get(key, None)


class MockApplication:
    config = MockConfig()

    def warn(self, *args, **kwargs):
        pass


class TestDotNetSphinxMapper:
    def test_create_class(self):
        """Test .NET class instance creation helper"""
        dom = dotnet.DotNetSphinxMapper(MockApplication())

        def _create_class(data):
            return list(dom.create_class(data))[0]

        cls = _create_class({"id": "Foo.Bar", "type": "Namespace"})
        assert isinstance(cls, dotnet.DotNetNamespace)
        cls = _create_class({"id": "Foo.Bar", "type": "Class"})
        assert isinstance(cls, dotnet.DotNetClass)
        cls = _create_class({"id": "Foo.Bar", "type": "Property"})
        assert isinstance(cls, dotnet.DotNetProperty)
        cls = _create_class({"id": "Foo.Bar", "type": "Method"})
        assert isinstance(cls, dotnet.DotNetMethod)
        cls = _create_class({"id": "Foo.Bar", "type": "Enum"})
        assert isinstance(cls, dotnet.DotNetEnum)
        cls = _create_class({"id": "Foo.Bar", "type": "Constructor"})
        assert isinstance(cls, dotnet.DotNetConstructor)
        cls = _create_class({"id": "Foo.Bar", "type": "Struct"})
        assert isinstance(cls, dotnet.DotNetStruct)
        cls = _create_class({"id": "Foo.Bar", "type": "Interface"})
        assert isinstance(cls, dotnet.DotNetInterface)
        cls = _create_class({"id": "Foo.Bar", "type": "Delegate"})
        assert isinstance(cls, dotnet.DotNetDelegate)
        cls = _create_class({"id": "Foo.Bar", "type": "Field"})
        assert isinstance(cls, dotnet.DotNetField)
        cls = _create_class({"id": "Foo.Bar", "type": "Event"})
        assert isinstance(cls, dotnet.DotNetEvent)

    def test_create_class_with_children(self):
        dom = dotnet.DotNetSphinxMapper(MockApplication())

        def _create_class(data):
            return list(dom.create_class(data))[0]

        cls = _create_class(
            {
                "id": "Foo.Bar",
                "type": "Class",
                "items": [{"id": "Foo.Bar.Baz", "type": "Method"}],
            }
        )
        assert isinstance(cls, dotnet.DotNetClass)
        assert cls.item_map == {}

    @patch("subprocess.check_output", lambda foo: foo)
    def test_get_objects(self):
        """Test basic get objects"""
        objs = []

        def _mock_find(self, patterns, **kwargs):
            return {"items": ["foo", "bar"]}

        def _mock_read(self, path):
            return {
                "items": [
                    {"id": "Foo.Bar", "name": "Foo", "type": "property"},
                    {"id": "Foo.Bar2", "name": "Bar", "type": "property"},
                ],
                "id": "Foo.Bar",
                "type": "Class",
                "summary": path,
            }

        with patch("autoapi.mappers.dotnet.DotNetSphinxMapper.find_files", _mock_find):
            with patch(
                "autoapi.mappers.dotnet.DotNetSphinxMapper.read_file", _mock_read
            ):
                dom = dotnet.DotNetSphinxMapper(MockApplication())
                dom.load("", "", "")
                dom.map()
                objs = dom.objects
                assert len(objs) == 2
                assert objs["Foo.Bar"].id == "Foo.Bar"
                assert objs["Foo.Bar"].name == "Foo.Bar"
                assert objs["Foo.Bar2"].id == "Foo.Bar2"
                assert objs["Foo.Bar2"].name == "Foo.Bar2"


class TestDotNetPythonMapper:
    def test_xml_parse(self):
        """XML doc comment parsing"""
        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'This is an example comment <see cref="FOO" />'
        )
        assert ret == "This is an example comment :any:`FOO`"

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'This is an example comment <see cref="!:FOO" />'
        )
        assert ret == "This is an example comment FOO"

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'This is an example comment <see cref="N:FOO">inner foo</see>'
        )
        assert ret == "This is an example comment :dn:ns:`FOO`"

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'Test <see cref="P:FOO" /> and <see cref="E:BAR">Blah</see>'
        )
        assert ret == "Test :dn:prop:`FOO` and :dn:event:`BAR`"

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'This is an example comment <paramref name="FOO" />'
        )
        assert ret == "This is an example comment ``FOO``"

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'This is an example comment <typeparamref name="FOO" />'
        )
        assert ret == "This is an example comment ``FOO``"

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'With surrounding characters s<see cref="FOO" />s'
        )
        assert ret == r"With surrounding characters s :any:`FOO`\s"

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'With surrounding characters s<paramref name="FOO" />s'
        )
        assert ret == r"With surrounding characters s ``FOO``\s"

    def test_xml_transform_escape(self):
        """XML transform escaping"""
        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'Foo <see cref="Foo`1" /> Bar'
        )
        assert ret == "Foo :any:`Foo\\`1` Bar"

        ret = dotnet.DotNetPythonMapper.transform_doc_comments(
            'No space before<see cref="M:Foo`1" />or after'
        )
        assert ret == "No space before :dn:meth:`Foo\\`1`\\or after"

    def test_parsing_obj(self):
        """Parse out object, test for transforms, etc"""
        obj = {
            "uid": "Foo`1",
            "name": "Foo<TUser>",
            "summary": 'Test parsing <see cref="Bar" />',
            "syntax": {
                "parameters": [
                    {
                        "id": "a",
                        "type": "{TUser}",
                        "description": 'Test <see cref="TUser" />',
                    }
                ],
                "return": {
                    "type": "Bar",
                    "description": (
                        'Test references <see cref="Bar" /> '
                        'and paramrefs <paramref name="a" />'
                    ),
                },
            },
        }
        mapped = dotnet.DotNetPythonMapper(obj, app=mock.MagicMock(), jinja_env=None)
        expected = {"name": "a", "type": "{TUser}", "desc": "Test :any:`TUser`"}
        assert mapped.parameters[0] == expected
        assert (
            mapped.returns["description"]
            == "Test references :any:`Bar` and paramrefs ``a``"
        )
