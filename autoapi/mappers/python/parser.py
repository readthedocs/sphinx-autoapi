import collections
import itertools
import os

import astroid
import astroid.builder
import sphinx.util.docstrings

from . import astroid_utils


def _prepare_docstring(doc):
    return "\n".join(sphinx.util.docstrings.prepare_docstring(doc))


class Parser:
    def __init__(self):
        self._qual_name_stack = []
        self._full_name_stack = []
        self._encoding = None

    def _get_qual_name(self, name):
        return ".".join(self._qual_name_stack + [name])

    def _get_full_name(self, name):
        return ".".join(self._full_name_stack + [name])

    def _parse_file(self, file_path, condition):
        directory, filename = os.path.split(file_path)
        module_parts = []
        if filename != "__init__.py":
            module_part = os.path.splitext(filename)[0]
            module_parts = [module_part]
        module_parts = collections.deque(module_parts)
        while directory and condition(directory):
            directory, module_part = os.path.split(directory)
            if module_part:
                module_parts.appendleft(module_part)

        module_name = ".".join(module_parts)
        node = astroid.builder.AstroidBuilder().file_build(file_path, module_name)
        return self.parse(node)

    def parse_file(self, file_path):
        return self._parse_file(
            file_path,
            lambda directory: os.path.isfile(os.path.join(directory, "__init__.py")),
        )

    def parse_file_in_namespace(self, file_path, dir_root):
        return self._parse_file(
            file_path, lambda directory: os.path.abspath(directory) != dir_root
        )

    def parse_annassign(self, node):
        # Don't document module level assignments to class attributes
        if isinstance(node.target, astroid.nodes.AssignAttr):
            return []

        return self._parse_assign(node)

    def parse_assign(self, node):
        # Don't document module level assignments to class attributes
        if any(isinstance(target, astroid.nodes.AssignAttr) for target in node.targets):
            return []

        return self._parse_assign(node)

    def _parse_assign(self, node):
        doc = ""
        doc_node = node.next_sibling()
        if isinstance(doc_node, astroid.nodes.Expr) and isinstance(
            doc_node.value, astroid.nodes.Const
        ):
            doc = doc_node.value.value

        type_ = "data"
        if isinstance(
            node.scope(), astroid.nodes.ClassDef
        ) or astroid_utils.is_constructor(node.scope()):
            type_ = "attribute"

        assign_value = astroid_utils.get_assign_value(node)
        if not assign_value:
            return []

        target = assign_value[0]
        value = assign_value[1]

        annotation = astroid_utils.get_assign_annotation(node)

        data = {
            "type": type_,
            "name": target,
            "qual_name": self._get_qual_name(target),
            "full_name": self._get_full_name(target),
            "doc": _prepare_docstring(doc),
            "value": value,
            "from_line_no": node.fromlineno,
            "to_line_no": node.tolineno,
            "annotation": annotation,
        }

        return [data]

    def parse_classdef(self, node, data=None):
        type_ = "class"
        if astroid_utils.is_exception(node):
            type_ = "exception"

        basenames = list(astroid_utils.get_full_basenames(node))

        data = {
            "type": type_,
            "name": node.name,
            "qual_name": self._get_qual_name(node.name),
            "full_name": self._get_full_name(node.name),
            "bases": basenames,
            "doc": _prepare_docstring(astroid_utils.get_class_docstring(node)),
            "from_line_no": node.fromlineno,
            "to_line_no": node.tolineno,
            "children": [],
        }

        self._qual_name_stack.append(node.name)
        self._full_name_stack.append(node.name)
        overridden = set()
        overloads = {}
        for base in itertools.chain(iter((node,)), node.ancestors()):
            seen = set()
            if base.qname() in (
                "__builtins__.object",
                "builtins.object",
                "builtins.type",
            ):
                continue
            for child in base.get_children():
                name = getattr(child, "name", None)
                if isinstance(child, (astroid.Assign, astroid.AnnAssign)):
                    assign_value = astroid_utils.get_assign_value(child)
                    if not assign_value:
                        continue
                    name = assign_value[0]

                if not name or name in overridden:
                    continue
                seen.add(name)
                child_data = self.parse(child)
                data["children"].extend(
                    _parse_child(node, child_data, overloads, base, name)
                )

            overridden.update(seen)

        self._qual_name_stack.pop()
        self._full_name_stack.pop()

        return [data]

    def parse_asyncfunctiondef(self, node):
        return self.parse_functiondef(node)

    def parse_functiondef(self, node):
        if astroid_utils.is_decorated_with_property_setter(node):
            return []

        type_ = "method"
        properties = []

        if node.type == "function":
            type_ = "function"

            if isinstance(node, astroid.AsyncFunctionDef):
                properties.append("async")
        elif astroid_utils.is_decorated_with_property(node):
            type_ = "property"
            if node.type == "classmethod":
                properties.append(node.type)
            if node.is_abstract(pass_is_abstract=False):
                properties.append("abstractmethod")
        else:
            # "__new__" method is implicit classmethod
            if node.type in ("staticmethod", "classmethod") and node.name != "__new__":
                properties.append(node.type)
            if node.is_abstract(pass_is_abstract=False):
                properties.append("abstractmethod")
            if isinstance(node, astroid.AsyncFunctionDef):
                properties.append("async")

        data = {
            "type": type_,
            "name": node.name,
            "qual_name": self._get_qual_name(node.name),
            "full_name": self._get_full_name(node.name),
            "args": astroid_utils.get_args_info(node.args),
            "doc": _prepare_docstring(astroid_utils.get_func_docstring(node)),
            "from_line_no": node.fromlineno,
            "to_line_no": node.tolineno,
            "return_annotation": astroid_utils.get_return_annotation(node),
            "properties": properties,
            "is_overload": astroid_utils.is_decorated_with_overload(node),
            "overloads": [],
        }

        result = [data]

        if node.name == "__init__":
            for child in node.get_children():
                if isinstance(child, (astroid.nodes.Assign, astroid.nodes.AnnAssign)):
                    child_data = self._parse_assign(child)
                    result.extend(data for data in child_data if data["doc"])

        return result

    def _parse_local_import_from(self, node):
        result = []

        for import_name, alias in node.names:
            is_wildcard = (alias or import_name) == "*"
            original_path = astroid_utils.get_full_import_name(
                node, alias or import_name
            )
            name = original_path if is_wildcard else (alias or import_name)
            qual_name = self._get_qual_name(alias or import_name)
            full_name = self._get_full_name(alias or import_name)

            data = {
                "type": "placeholder",
                "name": name,
                "qual_name": qual_name,
                "full_name": full_name,
                "original_path": original_path,
            }
            result.append(data)

        return result

    def parse_module(self, node):
        path = node.path
        if isinstance(node.path, list):
            path = node.path[0] if node.path else None

        type_ = "module"
        if node.package:
            type_ = "package"

        self._full_name_stack = [node.name]
        self._encoding = node.file_encoding

        data = {
            "type": type_,
            "name": node.name,
            "qual_name": node.name,
            "full_name": node.name,
            "doc": _prepare_docstring(node.doc_node.value if node.doc_node else ""),
            "children": [],
            "file_path": path,
            "encoding": node.file_encoding,
            "all": astroid_utils.get_module_all(node),
        }

        overloads = {}
        top_name = node.name.split(".", 1)[0]
        for child in node.get_children():
            if astroid_utils.is_local_import_from(child, top_name):
                child_data = self._parse_local_import_from(child)
            else:
                child_data = self.parse(child)

            data["children"].extend(_parse_child(node, child_data, overloads))

        return data

    def parse(self, node):
        data = {}

        node_type = node.__class__.__name__.lower()
        parse_func = getattr(self, "parse_" + node_type, None)
        if parse_func:
            data = parse_func(node)
        else:
            for child in node.get_children():
                data = self.parse(child)
                if data:
                    break
        return data


def _parse_child(node, child_data, overloads, base=None, name=None):
    result = []
    for single_data in child_data:
        if single_data["type"] in ("function", "method", "property"):
            if name is None:
                name = single_data["name"]
            if name in overloads:
                grouped = overloads[name]
                grouped["doc"] = single_data["doc"]
                if single_data["is_overload"]:
                    grouped["overloads"].append(
                        (single_data["args"], single_data["return_annotation"])
                    )
                continue
            if single_data["is_overload"] and name not in overloads:
                overloads[name] = single_data

        if base:
            single_data["inherited"] = base is not node
        result.append(single_data)

    return result
