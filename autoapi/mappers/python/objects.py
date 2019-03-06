import collections

from ..base import PythonMapperBase


class PythonPythonMapper(PythonMapperBase):

    language = "python"
    is_callable = False

    def __init__(self, obj, class_content="class", **kwargs):
        super(PythonPythonMapper, self).__init__(obj, **kwargs)

        self.name = obj["name"]
        self.id = obj.get("full_name", self.name)

        # Optional
        self.children = []
        self.args = obj.get("args")
        self.docstring = obj["doc"]

        # For later
        self.item_map = collections.defaultdict(list)
        self._class_content = class_content

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        self._args = value

    @property
    def docstring(self):
        return self._docstring

    @docstring.setter
    def docstring(self, value):
        self._docstring = value

    @property
    def is_undoc_member(self):
        return not bool(self.docstring)

    @property
    def is_private_member(self):
        return self.short_name.startswith("_") and not self.short_name.endswith("__")

    @property
    def is_special_member(self):
        return self.short_name.startswith("__") and self.short_name.endswith("__")

    @property
    def display(self):
        if self.is_undoc_member and "undoc-members" not in self.options:
            return False
        if self.is_private_member and "private-members" not in self.options:
            return False
        if self.is_special_member and "special-members" not in self.options:
            return False
        return True

    @property
    def summary(self):
        for line in self.docstring.splitlines():
            line = line.strip()
            if line:
                return line

        return ""

    def _children_of_type(self, type_):
        return list(child for child in self.children if child.type == type_)


class PythonFunction(PythonPythonMapper):
    type = "function"
    is_callable = True
    ref_directive = "func"


class PythonMethod(PythonPythonMapper):
    type = "method"
    is_callable = True
    ref_directive = "meth"

    def __init__(self, obj, **kwargs):
        super(PythonMethod, self).__init__(obj, **kwargs)

        self.method_type = obj["method_type"]

    @property
    def display(self):
        if self.short_name == "__init__":
            return False

        return super(PythonMethod, self).display


class PythonData(PythonPythonMapper):
    """Global, module level data."""

    type = "data"

    def __init__(self, obj, **kwargs):
        super(PythonData, self).__init__(obj, **kwargs)

        self.value = obj.get("value")


class PythonAttribute(PythonData):
    """An object/class level attribute."""

    type = "attribute"


class TopLevelPythonPythonMapper(PythonPythonMapper):
    ref_directive = "mod"
    _RENDER_LOG_LEVEL = "VERBOSE"

    def __init__(self, obj, **kwargs):
        super(TopLevelPythonPythonMapper, self).__init__(obj, **kwargs)

        self.top_level_object = "." not in self.name

        self.subpackages = []
        self.submodules = []
        self.all = obj["all"]

    @property
    def functions(self):
        return self._children_of_type("function")

    @property
    def classes(self):
        return self._children_of_type("class")


class PythonModule(TopLevelPythonPythonMapper):
    type = "module"


class PythonPackage(TopLevelPythonPythonMapper):
    type = "package"


class PythonClass(PythonPythonMapper):
    type = "class"

    def __init__(self, obj, **kwargs):
        super(PythonClass, self).__init__(obj, **kwargs)

        self.bases = obj["bases"]

    @PythonPythonMapper.args.getter
    def args(self):
        args = self._args

        constructor = self.constructor
        if constructor:
            args = constructor.args

        if args.startswith("self"):
            args = args[4:].lstrip(",").lstrip()

        return args

    @PythonPythonMapper.docstring.getter
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
