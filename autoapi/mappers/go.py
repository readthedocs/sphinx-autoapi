import json
import subprocess

import sphinx.util.logging

from .base import PythonMapperBase, SphinxMapperBase

LOGGER = sphinx.util.logging.getLogger(__name__)


class GoSphinxMapper(SphinxMapperBase):

    """Auto API domain handler for Go

    Parses directly from Go files.

    :param app: Sphinx application passed in as part of the extension
    """

    def load(self, patterns, dirs, ignore=None):
        """
        Load objects from the filesystem into the ``paths`` dictionary.

        """
        for _dir in dirs:
            data = self.read_file(_dir, ignore=ignore)
            if data:
                self.paths[_dir] = data

    def read_file(self, path, **kwargs):
        """Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        :param \**kwargs:
            * ignore (``list``): List of file patterns to ignore
        """
        # TODO support JSON here
        # TODO sphinx way of reporting errors in logs?

        parser_command = ["godocjson"]

        _ignore = kwargs.get("ignore")
        if _ignore:
            parser_command.extend(["-e", "{0}".format("|".join(_ignore))])

        parser_command.append(path)

        try:
            parsed_data = json.loads(subprocess.check_output(parser_command))
            return parsed_data
        except IOError:
            LOGGER.warning("Error reading file: {0}".format(path))
        except TypeError:
            LOGGER.warning("Error reading file: {0}".format(path))
        return None

    def create_class(self, data, options=None, **kwargs):
        """Return instance of class based on Go data

        Data keys handled here:

            _type
                Set the object class

            consts, types, vars, funcs
                Recurse into :py:meth:`create_class` to create child object
                instances

        :param data: dictionary data from godocjson output
        """
        _type = kwargs.get("_type")
        obj_map = dict((cls.type, cls) for cls in ALL_CLASSES)
        try:
            # Contextual type data from children recursion
            if _type:
                LOGGER.debug("Forcing Go Type %s" % _type)
                cls = obj_map[_type]
            else:
                cls = obj_map[data["type"]]
        except KeyError:
            LOGGER.warning("Unknown Type: %s" % data)
        else:
            if cls.inverted_names and "names" in data:
                # Handle types that have reversed names parameter
                for name in data["names"]:
                    data_inv = {}
                    data_inv.update(data)
                    data_inv["name"] = name
                    if "names" in data_inv:
                        del data_inv["names"]
                    for obj in self.create_class(data_inv):
                        yield obj
            else:
                # Recurse for children
                obj = cls(data, jinja_env=self.jinja_env)
                for child_type in ["consts", "types", "vars", "funcs"]:
                    for child_data in data.get(child_type, []):
                        obj.children += list(
                            self.create_class(
                                child_data,
                                _type=child_type.replace("consts", "const")
                                .replace("types", "type")
                                .replace("vars", "variable")
                                .replace("funcs", "func"),
                            )
                        )
                yield obj


class GoPythonMapper(PythonMapperBase):

    language = "go"
    inverted_names = False

    def __init__(self, obj, **kwargs):
        super(GoPythonMapper, self).__init__(obj, **kwargs)
        self.name = obj.get("name") or obj.get("packageName")
        self.id = self.name

        # Second level
        self.imports = obj.get("imports", [])
        self.children = []
        self.parameters = map(
            lambda n: {"name": n["name"], "type": n["type"].lstrip("*")},
            obj.get("parameters", []),
        )
        self.docstring = obj.get("doc", "")

        # Go Specific
        self.notes = obj.get("notes", {})
        self.filenames = obj.get("filenames", [])
        self.bugs = obj.get("bugs", [])

    def __str__(self):
        return "<{cls} {id}>".format(cls=self.__class__.__name__, id=self.id)

    @property
    def short_name(self):
        """Shorten name property"""
        return self.name.split(".")[-1]

    @property
    def namespace(self):
        pieces = self.id.split(".")[:-1]
        if pieces:
            return ".".join(pieces)
        return None

    @property
    def ref_type(self):
        return self.type

    @property
    def ref_directive(self):
        return self.type

    @property
    def methods(self):
        return self.obj.get("methods", [])


class GoVariable(GoPythonMapper):
    type = "var"
    inverted_names = True


class GoMethod(GoPythonMapper):
    type = "method"
    ref_directive = "meth"


class GoConstant(GoPythonMapper):
    type = "const"
    inverted_names = True


class GoFunction(GoPythonMapper):
    type = "func"
    ref_type = "function"


class GoPackage(GoPythonMapper):
    type = "package"
    ref_directive = "pkg"
    top_level_object = True
    _RENDER_LOG_LEVEL = "VERBOSE"


class GoType(GoPythonMapper):
    type = "type"


ALL_CLASSES = [GoConstant, GoFunction, GoPackage, GoVariable, GoType, GoMethod]
