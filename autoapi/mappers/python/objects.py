from typing import Optional

import sphinx.util.logging

from ..base import PythonMapperBase


LOGGER = sphinx.util.logging.getLogger(__name__)


class PythonPythonMapper(PythonMapperBase):
    """A base class for all types of representations of Python objects.

    :var name: The name given to this object.
    :vartype name: str
    :var id: A unique identifier for this object.
    :vartype id: str
    :var children: The members of this object.
    :vartype children: list(PythonPythonMapper)
    """

    language = "python"
    is_callable = False
    member_order = 0

    def __init__(self, obj, class_content="class", **kwargs):
        super(PythonPythonMapper, self).__init__(obj, **kwargs)

        self.name = obj["name"]
        self.id = obj.get("full_name", self.name)

        # Optional
        self.children = []
        self.args = obj.get("args")
        self.docstring = obj["doc"]
        self.imported = "original_path" in obj
        self.inherited = obj.get("inherited", False)
        """Whether this was inherited from an ancestor of the parent class.

        :type: bool
        """

        # For later
        self._class_content = class_content

        self._display_cache = None  # type: Optional[bool]

    @property
    def args(self):
        """The arguments to this object, formatted as a string.

        This will only be set for a function, method, or class.
        For classes, this does not include ``self``.

        :type: str or None
        """
        return self._args

    @args.setter
    def args(self, value):
        self._args = value

    @property
    def docstring(self):
        """The docstring for this object.

        If a docstring did not exist on the object,
        this will be the empty string.

        For classes this will also depend on the
        :confval:`autoapi_python_class_content` option.

        :type: str
        """
        return self._docstring

    @docstring.setter
    def docstring(self, value):
        self._docstring = value

    @property
    def is_undoc_member(self):
        """Whether this object has a docstring (False) or not (True).

        :type: bool
        """
        return not bool(self.docstring)

    @property
    def is_private_member(self):
        """Whether this object is private (True) or not (False).

        :type: bool
        """
        return self.short_name.startswith("_") and not self.short_name.endswith("__")

    @property
    def is_special_member(self):
        """Whether this object is a special member (True) or not (False).

        :type: bool
        """
        return self.short_name.startswith("__") and self.short_name.endswith("__")

    @property
    def display(self):
        """Whether this object should be displayed in documentation.

        This attribute depends on the configuration options given in
        :confval:`autoapi_options`.

        :type: bool
        """
        if self._display_cache is None:
            self._display_cache = not self._ask_ignore(self._should_skip())

        return self._display_cache

    @property
    def summary(self):
        """The summary line of the docstring.

        The summary line is the first non-empty line, as-per :pep:`257`.
        This will be the empty string if the object does not have a docstring.

        :type: str
        """
        for line in self.docstring.splitlines():
            line = line.strip()
            if line:
                return line

        return ""

    def _should_skip(self):  # type: () -> bool
        skip_undoc_member = self.is_undoc_member and "undoc-members" not in self.options
        skip_private_member = (
            self.is_private_member and "private-members" not in self.options
        )
        skip_special_member = (
            self.is_special_member and "special-members" not in self.options
        )
        skip_imported_member = self.imported and "imported-members" not in self.options

        return (
            skip_undoc_member
            or skip_private_member
            or skip_special_member
            or skip_imported_member
        )

    def _ask_ignore(self, skip):  # type: (bool) -> bool
        ask_result = self.app.emit_firstresult(
            "autoapi-skip-member", self.type, self.id, self, skip, self.options
        )

        return ask_result if ask_result is not None else skip

    def _children_of_type(self, type_):
        return list(child for child in self.children if child.type == type_)


class PythonFunction(PythonPythonMapper):
    type = "function"
    is_callable = True
    member_order = 40

    def __init__(self, obj, **kwargs):
        super(PythonFunction, self).__init__(obj, **kwargs)

        self.return_annotation = obj["return_annotation"]
        """The type annotation for the return type of this function.

        This will be ``None`` if an annotation
        or annotation comment was not given.

        :type: str or None
        """
        self.properties = obj["properties"]
        """The properties that describe what type of function this is.

        Can be only be: async

        :type: list(str)
        """
        self.overloads = obj["overloads"]
        """The list of overloaded signatures ``[(args, return_annotation), ...]`` of this function.

        :type: list(tuple(str, str))
        """


class PythonMethod(PythonFunction):
    type = "method"
    is_callable = True
    member_order = 50

    def __init__(self, obj, **kwargs):
        super(PythonMethod, self).__init__(obj, **kwargs)

        self.method_type = obj.get("method_type")
        """The type of method that this object represents.

        This can be one of: method, staticmethod, or classmethod.

        :type: str
        """
        self.properties = obj["properties"]
        """The properties that describe what type of method this is.

        Can be any of: abstractmethod, async, classmethod, property, staticmethod

        :type: list(str)
        """

    def _should_skip(self):  # type: () -> bool
        skip = super(PythonMethod, self)._should_skip() or self.name in (
            "__new__",
            "__init__",
        )
        return self._ask_ignore(skip)


class PythonData(PythonPythonMapper):
    """Global, module level data."""

    type = "data"
    member_order = 10

    def __init__(self, obj, **kwargs):
        super(PythonData, self).__init__(obj, **kwargs)

        self.value = obj.get("value")
        """The value of this attribute.

        This will be ``None`` if the value is not constant.

        :type: str or None
        """
        self.annotation = obj.get("annotation", obj.get("return_annotation"))
        """The type annotation of this attribute.

        This will be ``None`` if an annotation
        or annotation comment was not given.

        :type: str or None
        """


class PythonAttribute(PythonData):
    """An object/class level attribute."""

    type = "attribute"
    member_order = 10


class TopLevelPythonPythonMapper(PythonPythonMapper):
    _RENDER_LOG_LEVEL = "VERBOSE"

    def __init__(self, obj, **kwargs):
        super(TopLevelPythonPythonMapper, self).__init__(obj, **kwargs)

        self.top_level_object = "." not in self.name
        """Whether this object is at the very top level (True) or not (False).

        This will be False for subpackages and submodules.

        :type: bool
        """

        self.subpackages = []
        self.submodules = []
        self.all = obj["all"]
        """The contents of ``__all__`` if assigned to.

        Only constants are included.
        This will be ``None`` if no ``__all__`` was set.

        :type: list(str) or None
        """

    @property
    def functions(self):
        """All of the member functions.

        :type: list(PythonFunction)
        """
        return self._children_of_type("function")

    @property
    def classes(self):
        """All of the member classes.

        :type: list(PythonClass)
        """
        return self._children_of_type("class")


class PythonModule(TopLevelPythonPythonMapper):
    type = "module"


class PythonPackage(TopLevelPythonPythonMapper):
    type = "package"


class PythonClass(PythonPythonMapper):
    type = "class"
    member_order = 30

    def __init__(self, obj, **kwargs):
        super(PythonClass, self).__init__(obj, **kwargs)

        self.bases = obj["bases"]
        """The fully qualified names of all base classes.

        :type: list(str)
        """

    @property
    def args(self):
        args = self._args

        constructor = self.constructor
        if constructor:
            args = constructor.args

        if args.startswith("self"):
            args = args[4:].lstrip(",").lstrip()

        return args

    @args.setter
    def args(self, value):
        self._args = value

    @property
    def docstring(self):
        docstring = super(PythonClass, self).docstring

        if self._class_content in ("both", "init"):
            constructor_docstring = self.constructor_docstring

            if constructor_docstring:
                if self._class_content == "both":
                    docstring = "{0}\n{1}".format(docstring, constructor_docstring)
                else:
                    docstring = constructor_docstring

        return docstring

    @docstring.setter
    def docstring(self, value):
        self._docstring = value

    @property
    def methods(self):
        return self._children_of_type("method")

    @property
    def attributes(self):
        return self._children_of_type("attribute")

    @property
    def classes(self):
        return self._children_of_type("class")

    @property
    def constructor(self):
        for child in self.children:
            if child.short_name == "__init__":
                return child

        return None

    @property
    def constructor_docstring(self):
        docstring = ""

        constructor = self.constructor
        if constructor and constructor.docstring:
            docstring = constructor.docstring
        else:
            for child in self.children:
                if child.short_name == "__new__":
                    docstring = child.docstring
                    break

        return docstring


class PythonException(PythonClass):
    type = "exception"
    member_order = 20
