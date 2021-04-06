import collections
import copy
import operator
import os
import re

import sphinx.environment
import sphinx.util
from sphinx.util.console import bold
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
                LOGGER.warning(msg, type="autoapi", subtype="python_import_resolution")
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
            LOGGER.warning(msg, type="autoapi", subtype="python_import_resolution")
            module["children"].remove(child)
            children.pop(child["name"])
            continue

        if imported_from not in modules:
            msg = "Cannot resolve import of unknown module {0} in {1}".format(
                imported_from, module_name
            )
            LOGGER.warning(msg, type="autoapi", subtype="python_import_resolution")
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
            LOGGER.warning(msg, type="autoapi", subtype="python_import_resolution")
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
    # We are supposed to be resolving the placeholder,
    # not replacing it with another.
    assert original["type"] != "placeholder"
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


def _link_objs(value):
    result = ""

    delims = r"(\s*[\[\]\(\),]\s*)"
    delims_re = re.compile(delims)
    sub_targets = re.split(delims, value.strip())

    for sub_target in sub_targets:
        sub_target = sub_target.strip()
        if delims_re.match(sub_target):
            result += f"{sub_target}"
            if sub_target.endswith(","):
                result += " "
            else:
                result += "\\ "
        elif sub_target:
            result += f":py:obj:`{sub_target}`\\ "

    # Strip off the extra "\ "
    return result[:-2]


class PythonSphinxMapper(SphinxMapperBase):

    """Auto API domain handler for Python

    Parses directly from Python files.

    :param app: Sphinx application passed in as part of the extension
    """

    _OBJ_MAP = {
        cls.type: cls
        for cls in (
            PythonClass,
            PythonFunction,
            PythonModule,
            PythonMethod,
            PythonPackage,
            PythonAttribute,
            PythonData,
            PythonException,
        )
    }
    _OBJ_MAP["property"] = PythonMethod

    def __init__(self, app, template_dir=None, url_root=None):
        super(PythonSphinxMapper, self).__init__(app, template_dir, url_root)

        self.jinja_env.filters["link_objs"] = _link_objs
        self._use_implicit_namespace = (
            self.app.config.autoapi_python_use_implicit_namespaces
        )

    def _need_to_load(self, files):
        last_files = getattr(self.app.env, "autoapi_source_files", [])
        self.app.env.autoapi_source_files = files

        last_mtime = getattr(self.app.env, "autoapi_max_mtime", 0)
        this_mtime = max(os.path.getmtime(file) for _, file in files)
        self.app.env.autoapi_max_mtime = this_mtime

        if not self.app.config.autoapi_keep_files:
            return True

        if self.app.env.config_status != sphinx.environment.CONFIG_OK:
            return True

        return last_files != files or not last_mtime or last_mtime < this_mtime

    def _find_files(self, patterns, dirs, ignore):
        for dir_ in dirs:
            dir_root = dir_
            if (
                os.path.exists(os.path.join(dir_, "__init__.py"))
                or self._use_implicit_namespace
            ):
                dir_root = os.path.abspath(os.path.join(dir_, os.pardir))

            for path in self.find_files(patterns=patterns, dirs=[dir_], ignore=ignore):
                yield dir_root, path

    def load(self, patterns, dirs, ignore=None):
        """Load objects from the filesystem into the ``paths`` dictionary

        Also include an attribute on the object, ``relative_path`` which is the
        shortened, relative path the package/module
        """
        dir_root_files = list(self._find_files(patterns, dirs, ignore))
        if not self._need_to_load(dir_root_files):
            LOGGER.debug(
                "[AutoAPI] Skipping read stage because source files have not changed."
            )
            return False

        for dir_root, path in sphinx.util.status_iterator(
            dir_root_files,
            bold("[AutoAPI] Reading files... "),
            length=len(dir_root_files),
            stringify_func=(lambda x: x[1]),
        ):
            data = self.read_file(path=path, dir_root=dir_root)
            if data:
                data["relative_path"] = os.path.relpath(path, dir_root)
                self.paths[path] = data

        return True

    def read_file(self, path, **kwargs):
        """Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        """
        dir_root = kwargs.get("dir_root")
        try:
            if self._use_implicit_namespace:
                parsed_data = Parser().parse_file_in_namespace(path, dir_root)
            else:
                parsed_data = Parser().parse_file(path)
            return parsed_data
        except (IOError, TypeError, ImportError):
            LOGGER.debug("Reason:", exc_info=True)
            LOGGER.warning(
                "Unable to read file: {0}".format(path),
                type="autoapi",
                subtype="not_readable",
            )
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
        try:
            cls = self._OBJ_MAP[data["type"]]
        except KeyError:
            # this warning intentionally has no (sub-)type
            LOGGER.warning("Unknown type: %s" % data["type"])
        else:
            obj = cls(
                data,
                class_content=self.app.config.autoapi_python_class_content,
                options=self.app.config.autoapi_options,
                jinja_env=self.jinja_env,
                app=self.app,
                **kwargs,
            )
            obj.url_root = self.url_root

            lines = sphinx.util.docstrings.prepare_docstring(obj.docstring)
            if lines and "autodoc-process-docstring" in self.app.events.events:
                self.app.emit(
                    "autodoc-process-docstring", cls.type, obj.name, None, None, lines
                )
            obj.docstring = "\n".join(lines)
            self._record_typehints(obj)

            for child_data in data.get("children", []):
                for child_obj in self.create_class(
                    child_data, options=options, **kwargs
                ):
                    obj.children.append(child_obj)

            # Parser gives children in source order already
            if self.app.config.autoapi_member_order == "alphabetical":
                obj.children.sort(key=operator.attrgetter("name"))
            elif self.app.config.autoapi_member_order == "groupwise":
                obj.children.sort(key=lambda x: (x.member_order, x.name))

            yield obj

    def _record_typehints(self, obj):
        if isinstance(
            obj, (PythonClass, PythonFunction, PythonMethod)
        ) and not obj.obj.get("overloads"):
            obj_annotations = {}
            for _, name, annotation, _ in obj.obj["args"]:
                if name and annotation:
                    obj_annotations[name] = annotation

            return_annotation = obj.obj.get("return_annotation")
            if return_annotation:
                obj_annotations["return"] = return_annotation

            annotations = self.app.env.temp_data.setdefault("annotations", {})
            annotations[obj.id] = obj_annotations
