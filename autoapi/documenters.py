import re

import sphinx
from sphinx.ext import autodoc

from .mappers.python import (
    PythonFunction,
    PythonClass,
    PythonMethod,
    PythonData,
    PythonAttribute,
    PythonException,
)

# pylint: disable=attribute-defined-outside-init,no-self-use,unused-argument


class AutoapiDocumenter(autodoc.Documenter):
    def get_attr(self, obj, name, *defargs):
        if hasattr(self.env.app, "registry") and hasattr(
            self.env.app.registry, "autodoc_attrgettrs"
        ):
            attrgetters = self.env.app.registry.autodoc_attrgettrs
        else:
            # Needed for Sphinx 1.6
            attrgetters = getattr(autodoc.AutoDirective, "_special_attrgetters")

        for type_, func in attrgetters.items():
            if isinstance(obj, type_):
                return func(obj, name, *defargs)

        if name == "__doc__":
            return obj.docstring

        for child in obj.children:
            if child.name == name:
                return child

        if defargs:
            return defargs[0]

        raise AttributeError(name)

    def import_object(self):
        max_splits = self.fullname.count(".")
        for num_splits in range(max_splits, -1, -1):
            path_stack = list(reversed(self.fullname.rsplit(".", num_splits)))
            objects = self.env.autoapi_mapper.objects
            parent = objects.get(path_stack.pop())
            while parent and path_stack:
                parent = self.get_attr(parent, path_stack.pop(), None)

            if parent:
                self.object = parent
                self.object_name = parent.name
                return True

        return False

    def get_real_modname(self):
        # Return a fake modname so that nothing can be imported
        return None

    def get_doc(self, encoding=None, ignore=1):
        return [self.object.docstring.splitlines()]

    def process_doc(self, docstrings):
        for docstring in docstrings:
            for line in docstring:
                yield line

        yield ""

    def get_object_members(self, want_all):
        children = ((child.name, child) for child in self.object.children)

        if not want_all:
            if not self.options.members:
                return False, []

            children = (child for child in children if child[0] in self.options.members)
        elif not self.options.inherited_members:
            children = (child for child in children if not child[1].inherited)

        return False, sorted(children)


class _AutoapiDocstringSignatureMixin(object):  # pylint: disable=too-few-public-methods
    def format_signature(self, **kwargs):
        # Set "manual" attributes at the last possible moment.
        # This is to let a manual entry or docstring searching happen first,
        # and falling back to the discovered signature only when necessary.
        if self.args is None:
            self.args = self.object.args

        if self.retann is None:
            self.retann = self.object.return_annotation

        return super(_AutoapiDocstringSignatureMixin, self).format_signature(**kwargs)


class AutoapiFunctionDocumenter(
    AutoapiDocumenter, autodoc.FunctionDocumenter, _AutoapiDocstringSignatureMixin
):
    objtype = "apifunction"
    directivetype = "function"
    # Always prefer AutoapiDocumenters
    priority = autodoc.FunctionDocumenter.priority * 100 + 100

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, PythonFunction)

    def format_args(self, **kwargs):
        return "(" + self.object.args + ")"

    def add_directive_header(self, sig):
        if sphinx.version_info >= (2, 1):
            autodoc.Documenter.add_directive_header(self, sig)

            if "async" in self.object.properties:
                sourcename = self.get_sourcename()
                self.add_line("   :async:", sourcename)
        else:
            super(AutoapiFunctionDocumenter, self).add_directive_header(sig)


if sphinx.version_info >= (2,):

    class AutoapiDecoratorDocumenter(
        AutoapiFunctionDocumenter, AutoapiDocumenter, autodoc.DecoratorDocumenter
    ):
        objtype = "apidecorator"
        directivetype = "decorator"
        priority = autodoc.DecoratorDocumenter.priority * 100 + 100

        def format_signature(self, **kwargs):
            if self.args is None:
                self.args = self.format_args(**kwargs)

            return super(AutoapiDecoratorDocumenter, self).format_signature(**kwargs)

        def format_args(self, **kwargs):
            to_format = self.object.args

            if re.match(r"func\W", to_format) or to_format == "func":
                if "," not in to_format:
                    return None

                # We need to do better stripping here.
                # An annotation with a comma will mess this up.
                to_format = self.object.args.split(",", 1)[1]

            return "(" + to_format + ")"


class AutoapiClassDocumenter(
    AutoapiDocumenter, autodoc.ClassDocumenter, _AutoapiDocstringSignatureMixin
):
    objtype = "apiclass"
    directivetype = "class"
    doc_as_attr = False
    priority = autodoc.ClassDocumenter.priority * 100 + 100

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, PythonClass)

    def format_args(self, **kwargs):
        return "(" + self.object.args + ")"

    def add_directive_header(self, sig):
        autodoc.Documenter.add_directive_header(self, sig)

        if self.options.show_inheritance:
            sourcename = self.get_sourcename()
            self.add_line(u"", sourcename)

            # TODO: Change sphinx to allow overriding of getting base names
            if self.object.bases:
                bases = [":class:`{}`".format(base) for base in self.object.bases]
                self.add_line("   " + "Bases: {}".format(", ".join(bases)), sourcename)


class AutoapiMethodDocumenter(
    AutoapiDocumenter, autodoc.MethodDocumenter, _AutoapiDocstringSignatureMixin
):
    objtype = "apimethod"
    directivetype = "method"
    priority = autodoc.MethodDocumenter.priority * 100 + 100

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, PythonMethod)

    def format_args(self, **kwargs):
        return "(" + self.object.args + ")"

    def import_object(self):
        result = super(AutoapiMethodDocumenter, self).import_object()

        if result:
            if self.object.method_type != "method":
                if sphinx.version_info < (2, 1):
                    self.directivetype = self.object.method_type
                # document class and static members before ordinary ones
                self.member_order = self.member_order - 1

        return result

    def add_directive_header(self, sig):
        if sphinx.version_info >= (2, 1):
            autodoc.Documenter.add_directive_header(self, sig)

            sourcename = self.get_sourcename()
            for property_type in (
                "abstractmethod",
                "async",
                "classmethod",
                "staticmethod",
            ):
                if property_type in self.object.properties:
                    self.add_line("   :{}:".format(property_type), sourcename)
        else:
            autodoc.Documenter.add_directive_header(self, sig)


class AutoapiDataDocumenter(AutoapiDocumenter, autodoc.DataDocumenter):
    objtype = "apidata"
    directivetype = "data"
    priority = autodoc.DataDocumenter.priority * 100 + 100

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, PythonData)

    def add_directive_header(self, sig):
        autodoc.ModuleLevelDocumenter.add_directive_header(self, sig)
        sourcename = self.get_sourcename()
        if not self.options.annotation:
            # TODO: Change sphinx to allow overriding of object description
            if self.object.value is not None:
                self.add_line(
                    "   :annotation: = {}".format(self.object.value), sourcename
                )
        elif self.options.annotation is autodoc.SUPPRESS:
            pass
        else:
            self.add_line("   :annotation: %s" % self.options.annotation, sourcename)


class AutoapiAttributeDocumenter(AutoapiDocumenter, autodoc.AttributeDocumenter):
    objtype = "apiattribute"
    directivetype = "attribute"
    _datadescriptor = True
    priority = autodoc.AttributeDocumenter.priority * 100 + 100

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, PythonAttribute)

    def add_directive_header(self, sig):
        autodoc.ClassLevelDocumenter.add_directive_header(self, sig)
        sourcename = self.get_sourcename()
        if not self.options.annotation:
            # TODO: Change sphinx to allow overriding of object description
            if self.object.value is not None:
                self.add_line(
                    "   :annotation: = {}".format(self.object.value), sourcename
                )
        elif self.options.annotation is autodoc.SUPPRESS:
            pass
        else:
            self.add_line("   :annotation: %s" % self.options.annotation, sourcename)


class AutoapiModuleDocumenter(AutoapiDocumenter, autodoc.ModuleDocumenter):
    objtype = "apimodule"
    directivetype = "module"
    priority = autodoc.ModuleDocumenter.priority * 100 + 100


class AutoapiExceptionDocumenter(
    AutoapiClassDocumenter, AutoapiDocumenter, autodoc.ExceptionDocumenter
):
    objtype = "apiexception"
    directivetype = "exception"
    priority = autodoc.ExceptionDocumenter.priority * 100 + 100

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, PythonException)
