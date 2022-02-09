# coding=utf8

"""Test .NET autoapi objects"""

from collections import namedtuple
from unittest import mock
import os

from jinja2 import Environment, FileSystemLoader

from autoapi.mappers import dotnet
from autoapi.mappers import python
from autoapi.settings import TEMPLATE_DIR


class TestDotNetObject:
    def test_type(self):
        """Test types of some of the objects"""
        obj = dotnet.DotNetNamespace({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "namespace"
        assert obj.ref_type == "namespace"
        assert obj.ref_directive == "ns"

        obj = dotnet.DotNetMethod({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "method"
        assert obj.ref_type == "method"
        assert obj.ref_directive == "meth"

        obj = dotnet.DotNetProperty({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "property"
        assert obj.ref_type == "property"
        assert obj.ref_directive == "prop"

        obj = dotnet.DotNetEnum({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "enum"
        assert obj.ref_type == "enumeration"
        assert obj.ref_directive == "enum"

        obj = dotnet.DotNetStruct({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "struct"
        assert obj.ref_type == "structure"
        assert obj.ref_directive == "struct"

        obj = dotnet.DotNetConstructor({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "constructor"
        assert obj.ref_type == "constructor"
        assert obj.ref_directive == "ctor"

        obj = dotnet.DotNetInterface({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "interface"
        assert obj.ref_type == "interface"
        assert obj.ref_directive == "iface"

        obj = dotnet.DotNetDelegate({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "delegate"
        assert obj.ref_type == "delegate"
        assert obj.ref_directive == "del"

        obj = dotnet.DotNetClass({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "class"
        assert obj.ref_type == "class"
        assert obj.ref_directive == "cls"

        obj = dotnet.DotNetField({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "field"
        assert obj.ref_type == "field"
        assert obj.ref_directive == "field"

        obj = dotnet.DotNetEvent({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.type == "event"
        assert obj.ref_type == "event"
        assert obj.ref_directive == "event"

    def test_names(self):
        """Test names of objects"""
        obj = dotnet.DotNetNamespace({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert obj.name == "Foo.Bar"
        assert obj.short_name == "Bar"

        obj = dotnet.DotNetNamespace(
            {"id": "Foo.Bar.Something`1"}, jinja_env=None, app=None
        )
        assert obj.name == "Foo.Bar.Something`1"
        assert obj.short_name == "Something`1"

    def test_namespace_namespace(self):
        """Namespace parent resolution"""
        ns = dotnet.DotNetNamespace({"id": "Foo.Bar.Widgets"}, jinja_env=None, app=None)
        assert ns.namespace == "Foo.Bar"
        ns = dotnet.DotNetNamespace({"id": "Foo.Bar"}, jinja_env=None, app=None)
        assert ns.namespace == "Foo"
        ns = dotnet.DotNetNamespace({"id": "Foo"}, jinja_env=None, app=None)
        assert ns.namespace is None

    def test_class_namespace(self):
        """Class parent resolution"""
        cls = dotnet.DotNetClass(
            dict(id="Foo.Bar.Widget", type="class"),
            jinja_env=None,
            app=None,
        )
        assert cls.namespace == "Foo.Bar"
        cls = dotnet.DotNetClass(
            dict(id="Foo.Bar", type="class"), jinja_env=None, app=None
        )
        assert cls.namespace == "Foo"
        cls = dotnet.DotNetClass(dict(id="Foo", type="class"), jinja_env=None, app=None)
        assert cls.namespace is None

    def test_filename(self):
        """Object file name"""
        cls = dotnet.DotNetClass({"id": "Foo.Bar.Widget"}, jinja_env=None, app=None)
        assert cls.pathname == os.path.join("Foo", "Bar", "Widget")
        cls = dotnet.DotNetClass({"id": "Foo.Bar.Widget<T>"}, jinja_env=None, app=None)
        assert cls.pathname == os.path.join("Foo", "Bar", "Widget-T")
        cls = dotnet.DotNetClass(
            {"id": "Foo.Bar.Widget<T>(TFoo)"}, jinja_env=None, app=None
        )
        assert cls.pathname == os.path.join("Foo", "Bar", "Widget-T")
        cls = dotnet.DotNetClass(
            {"id": "Foo.Foo-Bar.Widget<T>(TFoo)"}, jinja_env=None, app=None
        )
        assert cls.pathname == os.path.join("Foo", "FooBar", "Widget-T")
        cls = dotnet.DotNetClass({"id": "Foo.Bär"}, jinja_env=None, app=None)
        assert cls.pathname == os.path.join("Foo", "Bar")
        cls = dotnet.DotNetClass({"id": "Ащщ.юИфк"}, jinja_env=None, app=None)
        assert cls.pathname == os.path.join("Ashchshch", "iuIfk")

    def test_rendered_class_escaping(self):
        """Rendered class escaping"""
        jinja_env = Environment(loader=FileSystemLoader([TEMPLATE_DIR]))
        cls = dotnet.DotNetClass(
            {"id": "Foo.Bar`1", "inheritance": ["Foo.Baz`1"]},
            jinja_env=jinja_env,
            app=mock.MagicMock(),
        )
        assert "* :dn:cls:`Foo.Baz\\`1`\n" in cls.render()

    def test_include_path(self):
        """Include path"""
        cls = dotnet.DotNetClass({"id": "Foo.Bar.Widget"}, jinja_env=None, app=None)
        assert cls.include_path == "/autoapi/Foo/Bar/Widget/index"
        cls = dotnet.DotNetClass({"id": "Foo.Bar.Widget"}, jinja_env=None, app=None)
        cls.url_root = "/autofoo"
        assert cls.include_path == "/autofoo/Foo/Bar/Widget/index"
