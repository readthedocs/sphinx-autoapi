# coding=utf8

"""Test .NET autoapi objects"""

import os
import unittest
from collections import namedtuple
import mock

from jinja2 import Environment, FileSystemLoader

from autoapi.mappers import dotnet
from autoapi.mappers import python
from autoapi.settings import TEMPLATE_DIR


class DotNetObjectTests(unittest.TestCase):
    def test_type(self):
        """Test types of some of the objects"""
        obj = dotnet.DotNetNamespace({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "namespace")
        self.assertEqual(obj.ref_type, "namespace")
        self.assertEqual(obj.ref_directive, "ns")

        obj = dotnet.DotNetMethod({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "method")
        self.assertEqual(obj.ref_type, "method")
        self.assertEqual(obj.ref_directive, "meth")

        obj = dotnet.DotNetProperty({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "property")
        self.assertEqual(obj.ref_type, "property")
        self.assertEqual(obj.ref_directive, "prop")

        obj = dotnet.DotNetEnum({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "enum")
        self.assertEqual(obj.ref_type, "enumeration")
        self.assertEqual(obj.ref_directive, "enum")

        obj = dotnet.DotNetStruct({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "struct")
        self.assertEqual(obj.ref_type, "structure")
        self.assertEqual(obj.ref_directive, "struct")

        obj = dotnet.DotNetConstructor({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "constructor")
        self.assertEqual(obj.ref_type, "constructor")
        self.assertEqual(obj.ref_directive, "ctor")

        obj = dotnet.DotNetInterface({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "interface")
        self.assertEqual(obj.ref_type, "interface")
        self.assertEqual(obj.ref_directive, "iface")

        obj = dotnet.DotNetDelegate({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "delegate")
        self.assertEqual(obj.ref_type, "delegate")
        self.assertEqual(obj.ref_directive, "del")

        obj = dotnet.DotNetClass({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "class")
        self.assertEqual(obj.ref_type, "class")
        self.assertEqual(obj.ref_directive, "cls")

        obj = dotnet.DotNetField({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "field")
        self.assertEqual(obj.ref_type, "field")
        self.assertEqual(obj.ref_directive, "field")

        obj = dotnet.DotNetEvent({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.type, "event")
        self.assertEqual(obj.ref_type, "event")
        self.assertEqual(obj.ref_directive, "event")

    def test_names(self):
        """Test names of objects"""
        obj = dotnet.DotNetNamespace({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(obj.name, "Foo.Bar")
        self.assertEqual(obj.short_name, "Bar")

        obj = dotnet.DotNetNamespace(
            {"id": "Foo.Bar.Something`1"}, jinja_env=None, app=None
        )
        self.assertEqual(obj.name, "Foo.Bar.Something`1")
        self.assertEqual(obj.short_name, "Something`1")

    def test_namespace_namespace(self):
        """Namespace parent resolution"""
        ns = dotnet.DotNetNamespace({"id": "Foo.Bar.Widgets"}, jinja_env=None, app=None)
        self.assertEqual(ns.namespace, "Foo.Bar")
        ns = dotnet.DotNetNamespace({"id": "Foo.Bar"}, jinja_env=None, app=None)
        self.assertEqual(ns.namespace, "Foo")
        ns = dotnet.DotNetNamespace({"id": "Foo"}, jinja_env=None, app=None)
        self.assertIsNone(ns.namespace)

    def test_class_namespace(self):
        """Class parent resolution"""
        cls = dotnet.DotNetClass(
            dict(id="Foo.Bar.Widget", type="class"), jinja_env=None, app=None,
        )
        self.assertEqual(cls.namespace, "Foo.Bar")
        cls = dotnet.DotNetClass(
            dict(id="Foo.Bar", type="class"), jinja_env=None, app=None
        )
        self.assertEqual(cls.namespace, "Foo")
        cls = dotnet.DotNetClass(dict(id="Foo", type="class"), jinja_env=None, app=None)
        self.assertIsNone(cls.namespace)

    def test_filename(self):
        """Object file name"""
        cls = dotnet.DotNetClass({"id": "Foo.Bar.Widget"}, jinja_env=None, app=None)
        self.assertEqual(cls.pathname, os.path.join("Foo", "Bar", "Widget"))
        cls = dotnet.DotNetClass({"id": "Foo.Bar.Widget<T>"}, jinja_env=None, app=None)
        self.assertEqual(cls.pathname, os.path.join("Foo", "Bar", "Widget-T"))
        cls = dotnet.DotNetClass(
            {"id": "Foo.Bar.Widget<T>(TFoo)"}, jinja_env=None, app=None
        )
        self.assertEqual(cls.pathname, os.path.join("Foo", "Bar", "Widget-T"))
        cls = dotnet.DotNetClass(
            {"id": "Foo.Foo-Bar.Widget<T>(TFoo)"}, jinja_env=None, app=None
        )
        self.assertEqual(cls.pathname, os.path.join("Foo", "FooBar", "Widget-T"))
        cls = dotnet.DotNetClass({"id": u"Foo.Bär"}, jinja_env=None, app=None)
        self.assertEqual(cls.pathname, os.path.join("Foo", "Bar"))
        cls = dotnet.DotNetClass({"id": u"Ащщ.юИфк"}, jinja_env=None, app=None)
        self.assertEqual(cls.pathname, os.path.join("Ashchshch", "iuIfk"))

    def test_rendered_class_escaping(self):
        """Rendered class escaping"""
        jinja_env = Environment(loader=FileSystemLoader([TEMPLATE_DIR]))
        cls = dotnet.DotNetClass(
            {"id": "Foo.Bar`1", "inheritance": ["Foo.Baz`1"]},
            jinja_env=jinja_env,
            app=mock.MagicMock(),
        )
        self.assertIn("* :dn:cls:`Foo.Baz\\`1`\n", cls.render())

    def test_include_path(self):
        """Include path"""
        cls = dotnet.DotNetClass({"id": "Foo.Bar.Widget"}, jinja_env=None, app=None)
        self.assertEqual(cls.include_path, "/autoapi/Foo/Bar/Widget/index")
        cls = dotnet.DotNetClass({"id": "Foo.Bar.Widget"}, jinja_env=None, app=None)
        cls.url_root = "/autofoo"
        self.assertEqual(cls.include_path, "/autofoo/Foo/Bar/Widget/index")
