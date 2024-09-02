import collections
import copy
import fnmatch
import itertools
import operator
import os
import re
import sys

from jinja2 import Environment, FileSystemLoader
import sphinx
import sphinx.environment
from sphinx.errors import ExtensionError
import sphinx.util
import sphinx.util.logging
from sphinx.util.console import colorize
from sphinx.util.display import status_iterator
import sphinx.util.docstrings
from sphinx.util.osutil import ensuredir

from ._parser import Parser
from ._objects import (
    PythonClass,
    PythonFunction,
    PythonModule,
    PythonMethod,
    PythonPackage,
    PythonProperty,
    PythonAttribute,
    PythonData,
    PythonException,
)
from .settings import OWN_PAGE_LEVELS, TEMPLATE_DIR

if sys.version_info < (3, 10):  # PY310
    from stdlib_list import in_stdlib
else:

    def in_stdlib(module_name: str) -> bool:
        return module_name in sys.stdlib_module_names


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
                msg = f"Invalid __all__ entry {name} in {original_module['name']}"
                LOGGER.warning(msg, type="autoapi", subtype="python_import_resolution")
                continue

            originals.append(originals_map[name])

    placeholders = []
    for original in originals:
        new_full_name = placeholder["full_name"].replace("*", original["name"])
        new_qual_name = placeholder["qual_name"].replace("*", original["name"])
        new_original_path = placeholder["original_path"].replace("*", original["name"])
        if "original_path" in original:
            new_original_path = original["original_path"]
        new_placeholder = dict(
            placeholder,
            name=original["name"],
            qual_name=new_qual_name,
            full_name=new_full_name,
            original_path=new_original_path,
        )
        placeholders.append(new_placeholder)

    return placeholders


def _resolve_module_placeholders(modules, module_name, visit_path, resolved):
    """Resolve all placeholder children under a module.

    Args:
        modules (dict(str, dict)): A mapping of module names to their
            data dictionary. Placeholders are resolved in place.
        module_name (str): The name of the module to resolve.
        visit_path: An ordered set of visited module names.
        visited (collections.OrderedDict)
        resolved (set(str)): A set of already resolved module names.
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
            visit_str = ", ".join(visit_path)
            msg = f"Cannot resolve cyclic import: {visit_str}, {imported_from}"
            LOGGER.warning(msg, type="autoapi", subtype="python_import_resolution")
            module["children"].remove(child)
            children.pop(child["name"])
            continue

        if imported_from not in modules:
            msg = (
                f"Cannot resolve import of unknown module {imported_from}"
                f" in {module_name}"
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
            msg = f"Cannot resolve import of {child['original_path']} in {module_name}"
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

    Args:
        placeholder (dict): The placeholder to resolve, in place.
        original (dict): The object that the placeholder represents.
    """
    new = copy.deepcopy(original)
    # We are supposed to be resolving the placeholder,
    # not replacing it with another.
    assert original["type"] != "placeholder"
    # The name remains the same.
    new["name"] = placeholder["name"]
    new["qual_name"] = placeholder["qual_name"]
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


class Mapper:
    """Base class for mapping `PythonMapperBase` objects to Sphinx.

    Args:
        app: Sphinx application instance
    """

    _OBJ_MAP = {
        cls.type: cls
        for cls in (
            PythonClass,
            PythonFunction,
            PythonModule,
            PythonMethod,
            PythonPackage,
            PythonProperty,
            PythonAttribute,
            PythonData,
            PythonException,
        )
    }

    def __init__(self, app, template_dir=None, dir_root=None, url_root=None):
        self.app = app

        template_paths = [TEMPLATE_DIR]

        if template_dir:
            # Put at the front so it's loaded first
            template_paths.insert(0, template_dir)

        self.jinja_env = Environment(
            loader=FileSystemLoader(template_paths),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        def _wrapped_prepare(value):
            return value

        self.jinja_env.filters["prepare_docstring"] = _wrapped_prepare
        if self.app.config.autoapi_prepare_jinja_env:
            self.app.config.autoapi_prepare_jinja_env(self.jinja_env)

        own_page_level = self.app.config.autoapi_own_page_level
        desired_page_level = OWN_PAGE_LEVELS.index(own_page_level)
        self.own_page_types = set(OWN_PAGE_LEVELS[: desired_page_level + 1])

        self.dir_root = dir_root
        self.url_root = url_root

        # Mapping of {filepath -> raw data}
        self.paths = collections.OrderedDict()
        # Mapping of {object id -> Python Object}
        self.objects_to_render = collections.OrderedDict()
        # Mapping of {object id -> Python Object}
        self.all_objects = collections.OrderedDict()
        # Mapping of {namespace id -> Python Object}
        self.namespaces = collections.OrderedDict()

        self.jinja_env.filters["link_objs"] = _link_objs
        self._use_implicit_namespace = (
            self.app.config.autoapi_python_use_implicit_namespaces
        )

    @staticmethod
    def find_files(patterns, dirs, ignore):
        if not ignore:
            ignore = []

        pattern_regexes = []
        for pattern in patterns:
            regex = re.compile(fnmatch.translate(pattern).replace(".*", "(.*)"))
            pattern_regexes.append((pattern, regex))

        for _dir in dirs:
            for root, _, filenames in os.walk(_dir):
                seen = set()
                for pattern, pattern_re in pattern_regexes:
                    for filename in fnmatch.filter(filenames, pattern):
                        skip = False

                        match = re.match(pattern_re, filename)
                        norm_name = match.groups()
                        if norm_name in seen:
                            continue

                        # Skip ignored files
                        for ignore_pattern in ignore:
                            if fnmatch.fnmatch(
                                os.path.join(root, filename), ignore_pattern
                            ):
                                LOGGER.info(
                                    colorize("bold", "[AutoAPI] ")
                                    + colorize(
                                        "darkgreen", f"Ignoring {root}/{filename}"
                                    )
                                )
                                skip = True

                        if skip:
                            continue

                        # Make sure the path is full
                        if not os.path.isabs(filename):
                            filename = os.path.join(root, filename)

                        yield filename
                        seen.add(norm_name)

    def output_rst(self, source_suffix):
        for _, obj in status_iterator(
            self.objects_to_render.items(),
            colorize("bold", "[AutoAPI] ") + "Rendering Data... ",
            length=len(self.objects_to_render),
            verbosity=1,
            stringify_func=(lambda x: x[0]),
        ):
            rst = obj.render(is_own_page=True)
            if not rst:
                continue

            output_dir = obj.output_dir(self.dir_root)
            ensuredir(output_dir)
            output_path = output_dir / obj.output_filename()
            path = f"{output_path}{source_suffix}"
            with open(path, "wb+") as detail_file:
                detail_file.write(rst.encode("utf-8"))

        if self.app.config.autoapi_add_toctree_entry:
            self._output_top_rst()

    def _output_top_rst(self):
        # Render Top Index
        top_level_index = os.path.join(self.dir_root, "index.rst")
        pages = [obj for obj in self.objects_to_render.values() if obj.display]
        if not pages:
            msg = (
                "No modules were rendered. "
                "Do you need to set autoapi_options to render additional objects?"
            )
            LOGGER.warning(msg, type="autoapi", subtype="nothing_rendered")
            return

        with open(top_level_index, "wb") as top_level_file:
            content = self.jinja_env.get_template("index.rst")
            top_level_file.write(content.render(pages=pages).encode("utf-8"))

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
                or os.path.exists(os.path.join(dir_, "__init__.pyi"))
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
        if not dir_root_files:
            raise ExtensionError(f"No source files found in: {','.join(dirs)}")

        if not self._need_to_load(dir_root_files):
            LOGGER.debug(
                "[AutoAPI] Skipping read stage because source files have not changed."
            )
            return False

        for dir_root, path in status_iterator(
            dir_root_files,
            colorize("bold", "[AutoAPI] Reading files... "),
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

        Args:
            path: Path of file to read
        """
        dir_root = kwargs.get("dir_root")
        try:
            if self._use_implicit_namespace:
                parsed_data = Parser().parse_file_in_namespace(path, dir_root)
            else:
                parsed_data = Parser().parse_file(path)
            return parsed_data
        except (OSError, TypeError, ImportError):
            LOGGER.debug("Reason:", exc_info=True)
            LOGGER.warning(
                f"Unable to read file: {path}",
                type="autoapi",
                subtype="not_readable",
            )
        return None

    def _skip_if_stdlib(self):
        documented_modules = {obj["full_name"] for obj in self.paths.values()}

        q = collections.deque(self.paths.values())
        while q:
            obj = q.popleft()
            if "children" in obj:
                q.extend(obj["children"])

            if obj.get("inherited", False):
                module = obj["inherited_from"]["full_name"].split(".", 1)[0]
                if (
                    in_stdlib(module)
                    and not obj["inherited_from"]["is_abstract"]
                    and module not in documented_modules
                ):
                    obj["hide"] = True

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

    def _hide_yo_kids(self):
        """For all direct children of a module/package, hide them if needed."""
        for module in self.paths.values():
            if module["all"] is not None:
                all_names = set(module["all"])
                for child in module["children"]:
                    if child["qual_name"] not in all_names:
                        child["hide"] = True
            elif module["type"] == "module":
                for child in module["children"]:
                    if "original_path" in child:
                        child["hide"] = True

    def map(self, options=None):
        self._skip_if_stdlib()
        self._resolve_placeholders()
        self._hide_yo_kids()
        self.app.env.autoapi_annotations = {}

        for _, data in status_iterator(
            self.paths.items(),
            colorize("bold", "[AutoAPI] ") + "Mapping Data... ",
            length=len(self.paths),
            stringify_func=(lambda x: x[0]),
        ):
            for obj in self.create_class(data, options=options):
                self.all_objects[obj.id] = obj

        self._create_module_hierarchy()
        self._render_selection()

        self.app.env.autoapi_objects = self.objects_to_render
        self.app.env.autoapi_all_objects = self.all_objects

    def _create_module_hierarchy(self) -> None:
        """Populate the sub{module,package}s attributes of all top level objects."""
        for obj in self.all_objects.values():
            parent_name = obj.name.rsplit(".", 1)[0]
            if parent_name in self.all_objects and parent_name != obj.name:
                parent = self.all_objects[parent_name]
                attr = f"sub{obj.type}s"
                getattr(parent, attr).append(obj)

        for obj in self.all_objects.values():
            obj.submodules.sort()
            obj.subpackages.sort()

    def _render_selection(self):
        """Propagate display values to children."""
        for obj in sorted(self.all_objects.values(), key=lambda obj: len(obj.id)):
            if obj.display:
                assert obj.type in self.own_page_types
                self.objects_to_render[obj.id] = obj
            else:
                for module in itertools.chain(obj.subpackages, obj.submodules):
                    module.obj["hide"] = True

        def _inner(parent):
            for child in parent.children:
                self.all_objects[child.id] = child
                if not parent.display:
                    child.obj["hide"] = True

                if child.display and child.type in self.own_page_types:
                    self.objects_to_render[child.id] = child

                _inner(child)

        for obj in list(self.all_objects.values()):
            _inner(obj)

    def create_class(self, data, options=None):
        """Create a class from the passed in data

        Args:
            data: dictionary data of parser output
        """
        try:
            cls = self._OBJ_MAP[data["type"]]
        except KeyError:
            # this warning intentionally has no (sub-)type
            LOGGER.warning(f"Unknown type: {data['type']}")
        else:
            obj = cls(
                data,
                class_content=self.app.config.autoapi_python_class_content,
                options=self.app.config.autoapi_options,
                jinja_env=self.jinja_env,
                app=self.app,
                url_root=self.url_root,
            )

            for child_data in data.get("children", []):
                for child_obj in self.create_class(child_data, options=options):
                    obj.children.append(child_obj)

            # Some objects require children to establish their docstring
            # or type annotations (eg classes with inheritance),
            # so do this after all children have been created.
            lines = obj.docstring.splitlines()
            if lines:
                # Add back the trailing newline that .splitlines removes
                lines.append("")
                if "autodoc-process-docstring" in self.app.events.events:
                    self.app.emit(
                        "autodoc-process-docstring",
                        cls.type,
                        obj.name,
                        None,
                        None,
                        lines,
                    )
            obj.docstring = "\n".join(lines)
            self._record_typehints(obj)

            # Parser gives children in source order already
            if self.app.config.autoapi_member_order == "alphabetical":
                obj.children.sort(key=operator.attrgetter("name"))
            elif self.app.config.autoapi_member_order == "groupwise":
                obj.children.sort(key=lambda x: (x.member_order, x.name))

            yield obj

    def _record_typehints(self, obj):
        if (
            isinstance(obj, (PythonClass, PythonFunction, PythonMethod))
            and not obj.overloads
        ) or isinstance(obj, PythonProperty):
            obj_annotations = {}

            include_return_annotation = True
            obj_data = obj.obj
            if isinstance(obj, PythonClass):
                constructor = obj.constructor
                if constructor:
                    include_return_annotation = False
                    obj_data = constructor.obj
                else:
                    return

            for _, name, annotation, _ in obj_data["args"]:
                if name and annotation:
                    obj_annotations[name] = annotation

            return_annotation = obj_data["return_annotation"]
            if include_return_annotation and return_annotation:
                obj_annotations["return"] = return_annotation

            self.app.env.autoapi_annotations[obj.id] = obj_annotations
