import collections
import os
import sys

import astroid
from . import astroid_utils

try:
    _TEXT_TYPE = unicode
except NameError:
    _TEXT_TYPE = str


class Parser(object):
    def __init__(self):
        self._name_stack = []
        self._encoding = None

    def _get_full_name(self, name):
        return ".".join(self._name_stack + [name])

    def _encode(self, to_encode):
        if self._encoding:
            try:
                return _TEXT_TYPE(to_encode, self._encoding)
            except TypeError:
                # The string was already in the correct format
                pass

        return to_encode

    def parse_file(self, file_path):
        directory, filename = os.path.split(file_path)
        module_parts = []
        if filename != "__init__.py":
            module_part = os.path.splitext(filename)[0]
            module_parts = [module_part]
        module_parts = collections.deque(module_parts)
        while os.path.isfile(os.path.join(directory, "__init__.py")):
            directory, module_part = os.path.split(directory)
            if module_part:
                module_parts.appendleft(module_part)

        module_name = ".".join(module_parts)
        node = astroid.MANAGER.ast_from_file(file_path, module_name, source=True)
        return self.parse(node)

    def parse_annassign(self, node):
        return self.parse_assign(node)

    def parse_assign(self, node):
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
        value = None
        try:
            value = self._encode(assign_value[1])
        except UnicodeDecodeError:
            # Ignore binary data on Python 2.7
            if sys.version_info[0] >= 3:
                raise

        annotation = astroid_utils.get_assign_annotation(node)

        data = {
            "type": type_,
            "name": target,
            "full_name": self._get_full_name(target),
            "doc": self._encode(doc),
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

        args = ""
        try:
            constructor = node.lookup("__init__")[1]
        except IndexError:
            pass
        else:
            if isinstance(constructor, astroid.nodes.FunctionDef):
                args = constructor.args.as_string()

        basenames = list(astroid_utils.get_full_basenames(node.bases, node.basenames))

        data = {
            "type": type_,
            "name": node.name,
            "full_name": self._get_full_name(node.name),
            "args": args,
            "bases": basenames,
            "doc": self._encode(node.doc or ""),
            "from_line_no": node.fromlineno,
            "to_line_no": node.tolineno,
            "children": [],
        }

        self._name_stack.append(node.name)
        for child in node.get_children():
            child_data = self.parse(child)
            if child_data:
                data["children"].extend(child_data)
        self._name_stack.pop()

        return [data]

    def _parse_property(self, node):
        data = {
            "type": "attribute",
            "name": node.name,
            "full_name": self._get_full_name(node.name),
            "doc": self._encode(node.doc or ""),
            "from_line_no": node.fromlineno,
            "to_line_no": node.tolineno,
        }

        return [data]

    def parse_functiondef(self, node):
        if astroid_utils.is_decorated_with_property(node):
            return self._parse_property(node)
        if astroid_utils.is_decorated_with_property_setter(node):
            return []

        type_ = "function" if node.type == "function" else "method"

        return_annotation = None
        if node.returns:
            return_annotation = node.returns.as_string()
        # Python 2 has no support for type annotations, so use getattr
        elif getattr(node, "type_comment_returns", None):
            return_annotation = node.type_comment_returns.as_string()

        data = {
            "type": type_,
            "name": node.name,
            "full_name": self._get_full_name(node.name),
            "args": node.args.as_string(),
            "doc": self._encode(node.doc or ""),
            "from_line_no": node.fromlineno,
            "to_line_no": node.tolineno,
            "return_annotation": return_annotation,
        }

        if type_ == "method":
            data["method_type"] = node.type

        result = [data]

        if node.name == "__init__":
            for child in node.get_children():
                if isinstance(child, (astroid.nodes.Assign, astroid.nodes.AnnAssign)):
                    child_data = self.parse_assign(child)
                    result.extend(data for data in child_data if data["doc"])

        return result

    def _parse_local_import_from(self, node):
        result = []

        for name, alias in node.names:
            is_wildcard = (alias or name) == "*"
            full_name = self._get_full_name(alias or name)
            original_path = astroid_utils.get_full_import_name(node, alias or name)

            data = {
                "type": "placeholder",
                "name": original_path if is_wildcard else (alias or name),
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

        self._name_stack = [node.name]
        self._encoding = node.file_encoding

        data = {
            "type": type_,
            "name": node.name,
            "full_name": node.name,
            "doc": self._encode(node.doc or ""),
            "children": [],
            "file_path": path,
            "encoding": node.file_encoding,
            "all": astroid_utils.get_module_all(node),
        }

        top_name = node.name.split(".", 1)[0]
        for child in node.get_children():
            if node.package and astroid_utils.is_local_import_from(child, top_name):
                child_data = self._parse_local_import_from(child)
            else:
                child_data = self.parse(child)

            if child_data:
                data["children"].extend(child_data)

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
