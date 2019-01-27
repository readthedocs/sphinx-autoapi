import json
import subprocess
import os

import sphinx.util.logging

from .base import PythonMapperBase, SphinxMapperBase

LOGGER = sphinx.util.logging.getLogger(__name__)


class JavaScriptSphinxMapper(SphinxMapperBase):

    """Auto API domain handler for Javascript

    Parses directly from Javascript files.

    :param app: Sphinx application passed in as part of the extension
    """

    def read_file(self, path, **kwargs):
        """Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        """
        # TODO support JSON here
        # TODO sphinx way of reporting errors in logs?
        subcmd = "jsdoc"
        if os.name == "nt":
            subcmd = ".".join([subcmd, "cmd"])

        try:
            parsed_data = json.loads(subprocess.check_output([subcmd, "-X", path]))
            return parsed_data
        except IOError:
            LOGGER.warning("Error reading file: {0}".format(path))
        except TypeError:
            LOGGER.warning("Error reading file: {0}".format(path))
        return None

    # Subclassed to iterate over items
    def map(self, options=None):
        """Trigger find of serialized sources and build objects"""
        for path, data in self.paths.items():
            for item in data:
                for obj in self.create_class(item, options):
                    obj.jinja_env = self.jinja_env
                    self.add_object(obj)

    def create_class(self, data, options=None, **kwargs):
        """Return instance of class based on Javascript data

        Data keys handled here:

            type
                Set the object class

            consts, types, vars, funcs
                Recurse into :py:meth:`create_class` to create child object
                instances

        :param data: dictionary data from godocjson output
        """
        obj_map = dict((cls.type, cls) for cls in ALL_CLASSES)
        try:
            cls = obj_map[data["kind"]]
        except (KeyError, TypeError):
            LOGGER.warning("Unknown Type: %s" % data)
        else:
            # Recurse for children
            obj = cls(data, jinja_env=self.jinja_env)
            if "children" in data:
                for child_data in data["children"]:
                    for child_obj in self.create_class(child_data, options=options):
                        obj.children.append(child_obj)
            yield obj


class JavaScriptPythonMapper(PythonMapperBase):

    language = "javascript"

    def __init__(self, obj, **kwargs):
        """
        Map JSON data into Python object.

        This is the standard object that will be rendered into the templates,
        so we try and keep standard naming to keep templates more re-usable.
        """

        super(JavaScriptPythonMapper, self).__init__(obj, **kwargs)
        self.name = obj.get("name")
        self.id = self.name

        # Second level
        self.docstring = obj.get("description", "")
        # self.docstring = obj.get('comment', '')

        self.imports = obj.get("imports", [])
        self.children = []
        self.parameters = map(
            lambda n: {"name": n["name"], "type": n["type"][0]}, obj.get("param", [])
        )

        # Language Specific
        pass


class JavaScriptClass(JavaScriptPythonMapper):
    type = "class"
    ref_directive = "class"
    top_level_object = True


class JavaScriptFunction(JavaScriptPythonMapper):
    type = "function"
    ref_type = "func"


class JavaScriptData(JavaScriptPythonMapper):
    type = "data"
    ref_directive = "data"


class JavaScriptMember(JavaScriptPythonMapper):
    type = "member"
    ref_directive = "member"


class JavaScriptAttribute(JavaScriptPythonMapper):
    type = "attribute"
    ref_directive = "attr"


ALL_CLASSES = [
    JavaScriptFunction,
    JavaScriptClass,
    JavaScriptData,
    JavaScriptAttribute,
    JavaScriptMember,
]
