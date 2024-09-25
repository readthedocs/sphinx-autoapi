import re

from sphinx.ext import autodoc

from ._objects import (
    PythonFunction,
    PythonClass,
    PythonMethod,
    PythonProperty,
    PythonData,
    PythonAttribute,
    PythonException,
)


class AutoapiDocumenter(autodoc.Documenter):
    def get_attr(self, obj, name, *defargs):
        attrgetters = self.env.app.registry.autodoc_attrgettrs

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
            objects = self.env.autoapi_objects
            parent = None
            current = objects.get(path_stack.pop())
            while current and path_stack:
                parent = current
                current = self.get_attr(current, path_stack.pop(), None)

            if current:
                self.object = current
                self.object_name = current.name
                self._method_parent = parent
                return True

        return False

    def get_real_modname(self):
        # Return a fake modname so that nothing can be imported
        return None

    def get_doc(self, encoding=None, ignore=1):
        return [self.object.docstring.splitlines()]

    def process_doc(self, docstrings):
        for docstring in docstrings:
            yield from docstring

        yield ""

    def get_object_members(self, want_all):
        children = (
            autodoc.ObjectMember(child.name, child) for child in self.object.children
        )

        if not want_all:
            if not self.options.members:
                return False, []

            children = (
                child for child in children if child.__name__ in self.options.members
            )
        elif not self.options.inherited_members:
            children = (child for child in children if not child.object.inherited)

        return False, children


class _AutoapiDocstringSignatureMixin:
    def format_signature(self, **kwargs):
        # Set "manual" attributes at the last possible moment.
        # This is to let a manual entry or docstring searching happen first,
        # and falling back to the discovered signature only when necessary.
        if self.args is None:
            self.args = self.object.args

        if self.retann is None:
            self.retann = self.object.return_annotation

        return super().format_signature(**kwargs)


class AutoapiFunctionDocumenter(
    AutoapiDocumenter, _AutoapiDocstringSignatureMixin, autodoc.FunctionDocumenter
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
        autodoc.Documenter.add_directive_header(self, sig)

        if "async" in self.object.properties:
            sourcename = self.get_sourcename()
            self.add_line("   :async:", sourcename)


class AutoapiDecoratorDocumenter(
    AutoapiFunctionDocumenter, AutoapiDocumenter, autodoc.DecoratorDocumenter
):
    objtype = "apidecorator"
    directivetype = "decorator"
    priority = autodoc.DecoratorDocumenter.priority * 100 + 100

    def format_signature(self, **kwargs):
        if self.args is None:
            self.args = self.format_args(**kwargs)

        return super().format_signature(**kwargs)

    def format_args(self, **kwargs):
        to_format = self.object.args

        if re.match(r"func\W", to_format) or to_format == "func":
            if "," not in to_format:
                return None

            # We need to do better stripping here.
            # An annotation with a comma will mess this up.
            to_format = self.object.args.split(",", 1)[1]

        return "(" + to_format + ")"


class AutoapiClassDocumenter(AutoapiDocumenter, autodoc.ClassDocumenter):
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
            self.add_line("", sourcename)

            # TODO: Change sphinx to allow overriding of getting base names
            if self.object.bases:
                bases = ", ".join(f":class:`{base}`" for base in self.object.bases)
                self.add_line(f"   Bases: {bases}", sourcename)

    def format_signature(self, **kwargs):
        # Set "manual" attributes at the last possible moment.
        # This is to let a manual entry or docstring searching happen first,
        # and falling back to the discovered signature only when necessary.
        if self.args is None:
            self.args = self.object.args

        return super().format_signature(**kwargs)


class AutoapiMethodDocumenter(
    AutoapiDocumenter, _AutoapiDocstringSignatureMixin, autodoc.MethodDocumenter
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
        result = super().import_object()

        if result:
            self.parent = self._method_parent
            if "staticmethod" in self.object.properties:
                # document static members before ordinary ones
                self.member_order = self.member_order - 2
            elif "classmethod" in self.object.properties:
                # document class members before ordinary ones but after static ones
                self.member_order = self.member_order - 1

        return result

    def add_directive_header(self, sig):
        autodoc.Documenter.add_directive_header(self, sig)

        sourcename = self.get_sourcename()
        for property_type in (
            "abstractmethod",
            "async",
            "classmethod",
            "staticmethod",
        ):
            if property_type in self.object.properties:
                self.add_line(f"   :{property_type}:", sourcename)


class AutoapiPropertyDocumenter(AutoapiDocumenter, autodoc.PropertyDocumenter):
    objtype = "apiproperty"
    directivetype = "property"
    priority = autodoc.PropertyDocumenter.priority * 100 + 100

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, PythonProperty)

    def add_directive_header(self, sig):
        autodoc.ClassLevelDocumenter.add_directive_header(self, sig)

        sourcename = self.get_sourcename()
        for property_type in (
            "abstractmethod",
            "classmethod",
        ):
            if property_type in self.object.properties:
                self.add_line(f"   :{property_type}:", sourcename)

        if self.object.annotation:
            self.add_line(f"   :type: {self.object.annotation}", sourcename)


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
            if self.object.value is not None:
                self.add_line(f"   :value: {self.object.value}", sourcename)
        elif self.options.annotation is autodoc.SUPPRESS:
            pass
        else:
            self.add_line(f"   :annotation: {self.options.annotation}", sourcename)

        if self.object.annotation:
            self.add_line(f"   :type: {self.object.annotation}", sourcename)


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
            if self.object.value is not None:
                self.add_line(f"   :value: {self.object.value}", sourcename)
        elif self.options.annotation is autodoc.SUPPRESS:
            pass
        else:
            self.add_line(f"   :annotation: {self.options.annotation}", sourcename)

        if self.object.annotation:
            self.add_line(f"   :type: {self.object.annotation}", sourcename)


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
