import functools
import pathlib
from typing import List, Optional

import sphinx.util.logging

from ..base import PythonMapperBase


LOGGER = sphinx.util.logging.getLogger(__name__)


def _format_args(args_info, include_annotations=True, ignore_self=None):
    result = []

    for i, (prefix, name, annotation, default) in enumerate(args_info):
        if i == 0 and ignore_self is not None and name == ignore_self:
            continue
        formatted = (
            (prefix or "")
            + (name or "")
            + (f": {annotation}" if annotation and include_annotations else "")
            + ((" = {}" if annotation else "={}").format(default) if default else "")
        )
        result.append(formatted)

    return ", ".join(result)


class PythonPythonMapper(PythonMapperBase):
    """A base class for all types of representations of Python objects.

    Attributes:
        name (str): The name given to this object.
        id (str): A unique identifier for this object.
        children (list(PythonPythonMapper)): The members of this object.
    """

    language = "python"
    is_callable = False
    member_order = 0
    type: str

    def __init__(self, obj, class_content="class", **kwargs) -> None:
        super().__init__(obj, **kwargs)

        self.name = obj["name"]
        self.qual_name = obj["qual_name"]
        self.id = obj.get("full_name", self.name)

        # Optional
        self.children: List[PythonPythonMapper] = []
        self._docstring = obj["doc"]
        self._docstring_resolved = False
        self.imported = "original_path" in obj
        self.inherited = obj.get("inherited", False)
        """Whether this was inherited from an ancestor of the parent class.

        :type: bool
        """

        # For later
        self._class_content = class_content

        self._display_cache: Optional[bool] = None

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
        self._docstring_resolved = True

    @property
    def is_top_level_object(self):
        """Whether this object is at the very top level (True) or not (False).

        This will be False for subpackages and submodules.

        :type: bool
        """
        return "." not in self.id

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
        :confval:`autoapi_options` and the result of :event:`autoapi-skip-member`.

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
        skip_inherited_member = (
            self.inherited and "inherited-members" not in self.options
        )

        return (
            skip_undoc_member
            or skip_private_member
            or skip_special_member
            or skip_imported_member
            or skip_inherited_member
        )

    def _ask_ignore(self, skip):  # type: (bool) -> bool
        ask_result = self.app.emit_firstresult(
            "autoapi-skip-member", self.type, self.id, self, skip, self.options
        )

        return ask_result if ask_result is not None else skip

    def _children_of_type(self, type_):
        return list(child for child in self.children if child.type == type_)


class PythonFunction(PythonPythonMapper):
    """The representation of a function."""

    type = "function"
    is_callable = True
    member_order = 30

    def __init__(self, obj, **kwargs):
        super().__init__(obj, **kwargs)

        autodoc_typehints = getattr(self.app.config, "autodoc_typehints", "signature")
        show_annotations = autodoc_typehints != "none" and not (
            autodoc_typehints == "description" and not obj["overloads"]
        )
        self.args = _format_args(obj["args"], show_annotations)
        """The arguments to this object, formatted as a string.

        :type: str
        """

        self.return_annotation = obj["return_annotation"] if show_annotations else None
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
        self.overloads = [
            (_format_args(args), return_annotation)
            for args, return_annotation in obj["overloads"]
        ]
        """The overloaded signatures of this function.

        Each tuple is a tuple of ``(args, return_annotation)``

        :type: list(tuple(str, str))
        """


class PythonMethod(PythonFunction):
    """The representation of a method."""

    type = "method"
    is_callable = True
    member_order = 50

    def __init__(self, obj, **kwargs):
        super().__init__(obj, **kwargs)

        self.properties = obj["properties"]
        """The properties that describe what type of method this is.

        Can be any of: abstractmethod, async, classmethod, property, staticmethod

        :type: list(str)
        """

    def _should_skip(self):  # type: () -> bool
        skip = super()._should_skip() or self.name in (
            "__new__",
            "__init__",
        )
        return self._ask_ignore(skip)


class PythonProperty(PythonPythonMapper):
    """The representation of a property on a class."""

    type = "property"
    member_order = 60

    def __init__(self, obj, **kwargs):
        super().__init__(obj, **kwargs)

        self.annotation = obj["return_annotation"]
        """The type annotation of this property.

        :type: str or None
        """
        self.properties = obj["properties"]
        """The properties that describe what type of property this is.

        Can be any of: abstractmethod, classmethod

        :type: list(str)
        """


class PythonData(PythonPythonMapper):
    """Global, module level data."""

    type = "data"
    member_order = 40

    def __init__(self, obj, **kwargs):
        super().__init__(obj, **kwargs)

        self.value = obj.get("value")
        """The value of this attribute.

        This will be ``None`` if the value is not constant.

        :type: str or None
        """
        self.annotation = obj.get("annotation")
        """The type annotation of this attribute.

        This will be ``None`` if an annotation
        or annotation comment was not given.

        :type: str or None
        """


class PythonAttribute(PythonData):
    """An object/class level attribute."""

    type = "attribute"
    member_order = 60


class TopLevelPythonPythonMapper(PythonPythonMapper):
    """A common base class for modules and packages."""

    _RENDER_LOG_LEVEL = "VERBOSE"

    def __init__(self, obj, **kwargs):
        super().__init__(obj, **kwargs)

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

    def output_dir(self, root):
        """The path to the file to render into, without a file suffix."""
        parts = [root] + self.name.split(".")
        return pathlib.PosixPath(*parts)

    def output_filename(self):
        """The path to the file to render into, without a file suffix."""
        return "index"


class PythonModule(TopLevelPythonPythonMapper):
    """The representation of a module."""

    type = "module"


class PythonPackage(TopLevelPythonPythonMapper):
    """The representation of a package."""

    type = "package"


class PythonClass(PythonPythonMapper):
    """The representation of a class."""

    type = "class"
    member_order = 20

    def __init__(self, obj, **kwargs):
        super().__init__(obj, **kwargs)

        self.bases = obj["bases"]
        """The fully qualified names of all base classes.

        :type: list(str)
        """

    @property
    def args(self):
        """The arguments to this object, formatted as a string.

        :type: str
        """
        args = ""

        if self.constructor:
            autodoc_typehints = getattr(
                self.app.config, "autodoc_typehints", "signature"
            )
            show_annotations = autodoc_typehints != "none" and not (
                autodoc_typehints == "description" and not self.constructor.overloads
            )
            args_data = self.constructor.obj["args"]
            args = _format_args(args_data, show_annotations, ignore_self="self")

        return args

    @property
    def overloads(self):
        overloads = []

        if self.constructor:
            overload_data = self.constructor.obj["overloads"]
            autodoc_typehints = getattr(
                self.app.config, "autodoc_typehints", "signature"
            )
            show_annotations = autodoc_typehints not in ("none", "description")
            overloads = [
                (
                    _format_args(args, show_annotations, ignore_self="self"),
                    return_annotation,
                )
                for args, return_annotation in overload_data
            ]

        return overloads

    @property
    def docstring(self):
        docstring = super().docstring

        if not self._docstring_resolved and self._class_content in ("both", "init"):
            constructor_docstring = self.constructor_docstring

            if constructor_docstring:
                if self._class_content == "both":
                    docstring = f"{docstring}\n{constructor_docstring}"
                else:
                    docstring = constructor_docstring

        return docstring

    @docstring.setter
    def docstring(self, value):
        super(PythonClass, self.__class__).docstring.fset(self, value)

    @property
    def methods(self):
        return self._children_of_type("method")

    @property
    def properties(self):
        return self._children_of_type("property")

    @property
    def attributes(self):
        return self._children_of_type("attribute")

    @property
    def classes(self):
        return self._children_of_type("class")

    @property
    @functools.lru_cache()
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
    """The representation of an exception class."""

    type = "exception"
    member_order = 10
