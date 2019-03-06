import collections
import copy
import os

import sphinx.util.docstrings
import sphinx.util.logging

from ..base import SphinxMapperBase
from .parser import Parser
from .objects import (
    PythonClass,
    PythonFunction,
    PythonModule,
    PythonMethod,
    PythonPackage,
    PythonAttribute,
    PythonData,
    PythonException,
)

LOGGER = sphinx.util.logging.getLogger(__name__)


def _expand_wildcard_placeholder(original_module, originals_map, placeholder):
    """Expand a wildcard placeholder to a sequence of named placeholders.

    :param original_module: The data dictionary of the module
        that the placeholder is imported from.
    :type original_module: dict
    :param originals_map: A map of the names of children under the module
        to their data dictionaries.
    :type originals_map: dict(str, dict)
    :param placeholder: The wildcard placeholder to expand.
    :type placeholder: dict

    :returns: The placeholders that the wildcard placeholder represents.
    :rtype: list(dict)
    """
    originals = originals_map.values()
    if original_module["all"] is not None:
        originals = []
        for name in original_module["all"]:
            if name == "__all__":
                continue

            if name not in originals_map:
                msg = "Invalid __all__ entry {0} in {1}".format(
                    name, original_module["name"]
                )
                LOGGER.warning(msg)
                continue

            originals.append(originals_map[name])

    placeholders = []
    for original in originals:
        new_full_name = placeholder["full_name"].replace("*", original["name"])
        new_original_path = placeholder["original_path"].replace("*", original["name"])
        if "original_path" in original:
            new_original_path = original["original_path"]
        new_placeholder = dict(
            placeholder,
            name=original["name"],
            full_name=new_full_name,
            original_path=new_original_path,
        )
        placeholders.append(new_placeholder)

    return placeholders


def _resolve_module_placeholders(modules, module_name, visit_path, resolved):
    """Resolve all placeholder children under a module.

    :param modules: A mapping of module names to their data dictionary.
        Placeholders are resolved in place.
    :type modules: dict(str, dict)
    :param module_name: The name of the module to resolve.
    :type module_name: str
    :param visit_path: An ordered set of visited module names.
    :type visited: collections.OrderedDict
    :param resolved: A set of already resolved module names.
    :type resolved: set(str)
    """
    if module_name in resolved:
        return

    visit_path[module_name] = True

    module, children = modules[module_name]
    for child in list(children.values()):
        if child["type"] != "placeholder":
            continue

        if child["original_path"] in modules:
            module["children"].remove(child)
            children.pop(child["name"])
            continue

        imported_from, original_name = child["original_path"].rsplit(".", 1)
        if imported_from in visit_path:
            msg = "Cannot resolve cyclic import: {0}, {1}".format(
                ", ".join(visit_path), imported_from
            )
            LOGGER.warning(msg)
            module["children"].remove(child)
            children.pop(child["name"])
            continue

        if imported_from not in modules:
            msg = "Cannot resolve import of unknown module {0} in {1}".format(
                imported_from, module_name
            )
            LOGGER.warning(msg)
            module["children"].remove(child)
            children.pop(child["name"])
            continue

        _resolve_module_placeholders(modules, imported_from, visit_path, resolved)

        if original_name == "*":
            original_module, originals_map = modules[imported_from]

            # Replace the wildcard placeholder
            # with a list of named placeholders.
            new_placeholders = _expand_wildcard_placeholder(
                original_module, originals_map, child
            )
            child_index = module["children"].index(child)
            module["children"][child_index : child_index + 1] = new_placeholders
            children.pop(child["name"])

            for new_placeholder in new_placeholders:
                if new_placeholder["name"] not in children:
                    children[new_placeholder["name"]] = new_placeholder
                original = originals_map[new_placeholder["name"]]
                _resolve_placeholder(new_placeholder, original)
        elif original_name not in modules[imported_from][1]:
            msg = "Cannot resolve import of {0} in {1}".format(
                child["original_path"], module_name
            )
            LOGGER.warning(msg)
            module["children"].remove(child)
            children.pop(child["name"])
            continue
        else:
            original = modules[imported_from][1][original_name]
            _resolve_placeholder(child, original)

    del visit_path[module_name]
    resolved.add(module_name)


def _resolve_placeholder(placeholder, original):
    """Resolve a placeholder to the given original object.

    :param placeholder: The placeholder to resolve, in place.
    :type placeholder: dict
    :param original: The object that the placeholder represents.
    :type original: dict
    """
    new = copy.deepcopy(original)
    # The name remains the same.
    new["name"] = placeholder["name"]
    new["full_name"] = placeholder["full_name"]
    # Record where the placeholder originally came from.
    new["original_path"] = original["full_name"]
    # The source lines for this placeholder do not exist in this file.
    # The keys might not exist if original is a resolved placeholder.
    new.pop("from_line_no", None)
    new.pop("to_line_no", None)

    # Resolve the children
    stack = list(new.get("children", ()))
    while stack:
        child = stack.pop()
        # Relocate the child to the new location
        assert child["full_name"].startswith(original["full_name"])
        suffix = child["full_name"][len(original["full_name"]) :]
        child["full_name"] = new["full_name"] + suffix
        # The source lines for this placeholder do not exist in this file.
        # The keys might not exist if original is a resolved placeholder.
        child.pop("from_line_no", None)
        child.pop("to_line_no", None)
        # Resolve the remaining children
        stack.extend(child.get("children", ()))

    placeholder.clear()
    placeholder.update(new)


class PythonSphinxMapper(SphinxMapperBase):

    """Auto API domain handler for Python

    Parses directly from Python files.

    :param app: Sphinx application passed in as part of the extension
    """

    def load(self, patterns, dirs, ignore=None):
        """Load objects from the filesystem into the ``paths`` dictionary

        Also include an attribute on the object, ``relative_path`` which is the
        shortened, relative path the package/module
        """
        for dir_ in dirs:
            dir_root = dir_
            if os.path.exists(os.path.join(dir_, "__init__.py")):
                dir_root = os.path.abspath(os.path.join(dir_, os.pardir))

            for path in self.find_files(patterns=patterns, dirs=[dir_], ignore=ignore):
                data = self.read_file(path=path)
                if data:
                    data["relative_path"] = os.path.relpath(path, dir_root)
                    self.paths[path] = data

    def read_file(self, path, **kwargs):
        """Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        """
        try:
            parsed_data = Parser().parse_file(path)
            return parsed_data
        except (IOError, TypeError, ImportError):
            LOGGER.warning("Error reading file: {0}".format(path))
        return None

    def _resolve_placeholders(self):
        """Resolve objects that have been imported from elsewhere."""
        modules = {}
        for module in self.paths.values():
            children = {child["name"]: child for child in module["children"]}
            modules[module["name"]] = (module, children)

        resolved = set()
        for module_name in modules:
            visit_path = collections.OrderedDict()
            _resolve_module_placeholders(modules, module_name, visit_path, resolved)

    def map(self, options=None):
        self._resolve_placeholders()

        super(PythonSphinxMapper, self).map(options)

        parents = {obj.name: obj for obj in self.objects.values()}
        for obj in self.objects.values():
            parent_name = obj.name.rsplit(".", 1)[0]
            if parent_name in parents and parent_name != obj.name:
                parent = parents[parent_name]
                attr = "sub{}s".format(obj.type)
                getattr(parent, attr).append(obj)

        for obj in self.objects.values():
            obj.submodules.sort()
            obj.subpackages.sort()

    def create_class(self, data, options=None, **kwargs):
        """Create a class from the passed in data

        :param data: dictionary data of parser output
        """
        obj_map = dict(
            (cls.type, cls)
            for cls in [
                PythonClass,
                PythonFunction,
                PythonModule,
                PythonMethod,
                PythonPackage,
                PythonAttribute,
                PythonData,
                PythonException,
            ]
        )
        try:
            cls = obj_map[data["type"]]
        except KeyError:
            LOGGER.warning("Unknown type: %s" % data["type"])
        else:
            obj = cls(
                data,
                class_content=self.app.config.autoapi_python_class_content,
                options=self.app.config.autoapi_options,
                jinja_env=self.jinja_env,
                url_root=self.url_root,
                **kwargs
            )

            lines = sphinx.util.docstrings.prepare_docstring(obj.docstring)
            if lines and "autodoc-process-docstring" in self.app.events.events:
                self.app.emit(
                    "autodoc-process-docstring",
                    cls.type,
                    obj.name,
                    None,  # object
                    None,  # options
                    lines,
                )
            obj.docstring = "\n".join(lines)

            for child_data in data.get("children", []):
                for child_obj in self.create_class(
                    child_data, options=options, **kwargs
                ):
                    obj.children.append(child_obj)
            yield obj
