from __future__ import annotations

import functools
import pathlib

import sphinx
import sphinx.util
import sphinx.util.logging

from .settings import OWN_PAGE_LEVELS

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


class PythonObject:
    """A class representing an entity from the parsed source code.

    This class turns the dictionaries output by the parser into an object.

    Args:
        obj: JSON object representing this object
        jinja_env: A template environment for rendering this object
    """

    member_order = 0
    """The ordering of objects when doing "groupwise" sorting."""
    type: str

    def __init__(
        self, obj, jinja_env, app, url_root, options=None, class_content="class"
    ):
        self.app = app
        self.obj = obj
        self.options = options
        self.jinja_env = jinja_env
        self.url_root = url_root

        self.name: str = obj["name"]
        """The name of the object, as named in the parsed source code.

        This name will have no periods in it.
        """
        self.qual_name: str = obj["qual_name"]
        """The qualified name for this object."""
        self.id: str = obj.get("full_name", self.name)
        """A globally unique identifier for this object.

        This is the same as the fully qualified name of the object.
        """

        self.children: list[PythonObject] = []
        """The members of this object.

        For example, the classes and functions defined in the parent module.
        """
        self._docstring: str = obj["doc"]
        self.imported: bool = "original_path" in obj
        """Whether this object was imported from another module."""
        self.inherited: bool = obj.get("inherited", False)
        """Whether this was inherited from an ancestor of the parent class."""

        # For later
        self._class_content = class_content
        self._display_cache: bool | None = None

    def __getstate__(self):
        """Obtains serialisable data for pickling."""
        __dict__ = self.__dict__.copy()
        __dict__.update(app=None, jinja_env=None)  # clear unpickable attributes
        return __dict__

    def render(self, **kwargs):
        LOGGER.log("VERBOSE", "Rendering %s", self.id)

        template = self.jinja_env.get_template(f"python/{self.type}.rst")

        ctx = {}
        ctx.update(**self.get_context_data())
        ctx.update(**kwargs)
        return template.render(**ctx)

    @property
    def rendered(self):
        """Shortcut to render an object in templates."""
        return self.render()

    def get_context_data(self):
        own_page_level = self.app.config.autoapi_own_page_level
        desired_page_level = OWN_PAGE_LEVELS.index(own_page_level)
        own_page_types = set(OWN_PAGE_LEVELS[: desired_page_level + 1])

        return {
            "autoapi_options": self.app.config.autoapi_options,
            "include_summaries": self.app.config.autoapi_include_summaries,
            "obj": self,
            "own_page_types": own_page_types,
            "sphinx_version": sphinx.version_info,
        }

    def __lt__(self, other):
        """Object sorting comparison"""
        if not isinstance(other, PythonObject):
            return NotImplemented

        return self.id < other.id

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} {self.id}>"

    @property
    def short_name(self) -> str:
        """Shorten name property"""
        return self.name.split(".")[-1]

    def output_dir(self, root):
        """The directory to render this object."""
        module = self.id[: -(len("." + self.qual_name))]
        parts = [root] + module.split(".")
        return pathlib.PurePosixPath(*parts)

    def output_filename(self) -> str:
        """The name of the file to render into, without a file suffix."""
        filename = self.qual_name
        if filename == "index":
            filename = ".index"

        return filename

    @property
    def include_path(self) -> str:
        """Return 'absolute' path without regarding OS path separator

        This is used in ``toctree`` directives, as Sphinx always expects Unix
        path separators
        """
        return str(self.output_dir(self.url_root) / self.output_filename())

    @property
    def docstring(self) -> str:
        """The docstring for this object.

        If a docstring did not exist on the object,
        this will be the empty string.

        For classes, this will also depend on the
        :confval:`autoapi_python_class_content` option.
        """
        return self._docstring

    @docstring.setter
    def docstring(self, value: str) -> None:
        self._docstring = value
        self._docstring_resolved = True

    @property
    def is_top_level_object(self) -> bool:
        """Whether this object is at the very top level (True) or not (False).

        This will be False for subpackages and submodules.
        """
        return "." not in self.id

    @property
    def is_undoc_member(self) -> bool:
        """Whether this object has a docstring (False) or not (True)."""
        return not bool(self.docstring)

    @property
    def is_private_member(self) -> bool:
        """Whether this object is private (True) or not (False)."""
        return self.short_name.startswith("_") and not self.short_name.endswith("__")

    @property
    def is_special_member(self) -> bool:
        """Whether this object is a special member (True) or not (False)."""
        return self.short_name.startswith("__") and self.short_name.endswith("__")

    @property
    def display(self) -> bool:
        """Whether this object should be displayed in documentation.

        This attribute depends on the configuration options given in
        :confval:`autoapi_options` and the result of :event:`autoapi-skip-member`.
        """
        if self._display_cache is None:
            self._display_cache = not self._ask_ignore(self._should_skip())

        return self._display_cache

    @property
    def summary(self) -> str:
        """The summary line of the docstring.

        The summary line is the first non-empty line, as-per :pep:`257`.
        This will be the empty string if the object does not have a docstring.
        """
        for line in self.docstring.splitlines():
            line = line.strip()
            if line:
                return line

        return ""

    def _should_skip(self) -> bool:
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
            self.obj.get("hide", False)
            or skip_undoc_member
            or skip_private_member
            or skip_special_member
            or skip_imported_member
            or skip_inherited_member
        )

    def _ask_ignore(self, skip: bool) -> bool:
        ask_result = self.app.emit_firstresult(
            "autoapi-skip-member", self.type, self.id, self, skip, self.options
        )

        return ask_result if ask_result is not None else skip

    def _children_of_type(self, type_: str) -> list[PythonObject]:
        return list(child for child in self.children if child.type == type_)


class PythonFunction(PythonObject):
    """The representation of a function."""

    type = "function"
    member_order = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        autodoc_typehints = getattr(self.app.config, "autodoc_typehints", "signature")
        show_annotations = autodoc_typehints != "none" and not (
            autodoc_typehints == "description" and not self.obj["overloads"]
        )
        self.args: str = _format_args(self.obj["args"], show_annotations)
        """The arguments to this object, formatted as a string."""

        self.return_annotation: str | None = (
            self.obj["return_annotation"] if show_annotations else None
        )
        """The type annotation for the return type of this function.

        This will be ``None`` if an annotation
        or annotation comment was not given.
        """
        self.properties: list[str] = self.obj["properties"]
        """The properties that describe what type of function this is.

        Can be only be: async.
        """
        self.overloads: list[tuple[str, str]] = [
            (_format_args(args), return_annotation)
            for args, return_annotation in self.obj["overloads"]
        ]
        """The overloaded signatures of this function.

        Each tuple is a tuple of ``(args, return_annotation)``
        """


class PythonMethod(PythonFunction):
    """The representation of a method."""

    type = "method"
    member_order = 50

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.properties: list[str] = self.obj["properties"]
        """The properties that describe what type of method this is.

        Can be any of: abstractmethod, async, classmethod, property, staticmethod.
        """

    def _should_skip(self) -> bool:
        return super()._should_skip() or self.name in (
            "__new__",
            "__init__",
        )


class PythonProperty(PythonObject):
    """The representation of a property on a class."""

    type = "property"
    member_order = 60

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.annotation: str | None = self.obj["return_annotation"]
        """The type annotation of this property."""
        self.properties: list[str] = self.obj["properties"]
        """The properties that describe what type of property this is.

        Can be any of: abstractmethod, classmethod.
        """


class PythonData(PythonObject):
    """Global, module level data."""

    type = "data"
    member_order = 40

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.value: str | None = self.obj.get("value")
        """The value of this attribute.

        This will be ``None`` if the value is not constant.
        """
        self.annotation: str | None = self.obj.get("annotation")
        """The type annotation of this attribute.

        This will be ``None`` if an annotation
        or annotation comment was not given.
        """


class PythonAttribute(PythonData):
    """An object/class level attribute."""

    type = "attribute"
    member_order = 60


class TopLevelPythonPythonMapper(PythonObject):
    """A common base class for modules and packages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.subpackages = []
        self.submodules = []
        self.all = self.obj["all"]
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
        return pathlib.PurePosixPath(*parts)

    def output_filename(self):
        """The path to the file to render into, without a file suffix."""
        return "index"


class PythonModule(TopLevelPythonPythonMapper):
    """The representation of a module."""

    type = "module"


class PythonPackage(TopLevelPythonPythonMapper):
    """The representation of a package."""

    type = "package"


class PythonClass(PythonObject):
    """The representation of a class."""

    type = "class"
    member_order = 20

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bases: list[str] = self.obj["bases"]
        """The fully qualified names of all base classes."""

        self._docstring_resolved: bool = False

    @property
    def args(self) -> str:
        """The arguments to this object, formatted as a string."""
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
    def overloads(self) -> list[tuple[str, str]]:
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
    def docstring(self) -> str:
        docstring = self._docstring

        if not self._docstring_resolved and self._class_content in ("both", "init"):
            constructor_docstring = self.constructor_docstring

            if constructor_docstring:
                if self._class_content == "both":
                    docstring = f"{docstring}\n{constructor_docstring}"
                else:
                    docstring = constructor_docstring

        return docstring

    @docstring.setter
    def docstring(self, value: str) -> None:
        self._docstring = value
        self._docstring_resolved = True

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
    @functools.lru_cache
    def constructor(self):
        for child in self.children:
            if child.short_name == "__init__":
                if not child.type == "method":
                    break

                return child

        return None

    @property
    def constructor_docstring(self) -> str:
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
