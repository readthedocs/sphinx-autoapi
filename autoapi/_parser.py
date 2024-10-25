import collections
import os

import astroid
import astroid.builder
import sphinx.util.docstrings

from . import _astroid_utils


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
        if filename != "__init__.py" and filename != "__init__.pyi":
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
            lambda directory: (
                os.path.isfile(os.path.join(directory, "__init__.py"))
                or os.path.isfile(os.path.join(directory, "__init__.pyi"))
            ),
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
        ) or _astroid_utils.is_constructor(node.scope()):
            type_ = "attribute"

        assign_value = _astroid_utils.get_assign_value(node)
        if not assign_value:
            return []

        target = assign_value[0]
        value = assign_value[1]

        annotation = _astroid_utils.get_assign_annotation(node)
        if annotation in ("TypeAlias", "typing.TypeAlias"):
            value = node.value.as_string()

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

    def _parse_classdef(self, node, use_name_stacks):
        if use_name_stacks:
            qual_name = self._get_qual_name(node.name)
            full_name = self._get_full_name(node.name)

            self._qual_name_stack.append(node.name)
            self._full_name_stack.append(node.name)
        else:
            qual_name = node.qname()[len(node.root().qname()) + 1 :]
            full_name = node.qname()

        type_ = "class"
        if _astroid_utils.is_exception(node):
            type_ = "exception"

        data = {
            "type": type_,
            "name": node.name,
            "qual_name": qual_name,
            "full_name": full_name,
            "bases": list(_astroid_utils.get_full_basenames(node)),
            "doc": _prepare_docstring(_astroid_utils.get_class_docstring(node)),
            "from_line_no": node.fromlineno,
            "to_line_no": node.tolineno,
            "children": [],
            "is_abstract": _astroid_utils.is_abstract_class(node),
        }

        overloads = {}
        for child in node.get_children():
            children_data = self.parse(child)
            for child_data in children_data:
                if _parse_child(child_data, overloads):
                    data["children"].append(child_data)

        data["children"] = list(self._resolve_inheritance(data))

        return data

    def _resolve_inheritance(self, *mro_data):
        overridden = set()
        children = {}
        for i, cls_data in enumerate(mro_data):
            seen = set()
            base_children = []
            overloads = {}

            for child_data in cls_data["children"]:
                name = child_data["name"]

                existing_child = children.get(name)
                if existing_child and not existing_child["doc"]:
                    existing_child["doc"] = child_data["doc"]

                if name in overridden:
                    continue

                seen.add(name)
                if _parse_child(child_data, overloads):
                    base_children.append(child_data)
                    child_data["inherited"] = i != 0
                    if child_data["inherited"]:
                        child_data["inherited_from"] = cls_data

            overridden.update(seen)

            for base_child in base_children:
                existing_child = children.get(base_child["name"])
                if (
                    existing_child
                    # If an attribute was assigned to but this class has a property
                    # with the same name, then the property was assigned to,
                    # and not an attribute.
                    and not (
                        base_child["type"] == "property"
                        and existing_child["type"] == "attribute"
                    )
                ):
                    continue

                children[base_child["name"]] = base_child

        return children.values()

    def _relevant_ancestors(self, node):
        for base in node.ancestors():
            if base.qname() in (
                "__builtins__.object",
                "builtins.object",
                "builtins.type",
            ):
                continue

            yield base

    def parse_classdef(self, node):
        data = self._parse_classdef(node, use_name_stacks=True)

        ancestors = self._relevant_ancestors(node)
        ancestor_data = [
            self._parse_classdef(base, use_name_stacks=False) for base in ancestors
        ]
        if ancestor_data:
            data["children"] = list(self._resolve_inheritance(data, *ancestor_data))

        self._qual_name_stack.pop()
        self._full_name_stack.pop()

        return [data]

    def parse_asyncfunctiondef(self, node):
        return self.parse_functiondef(node)

    def parse_functiondef(self, node):
        if _astroid_utils.is_decorated_with_property_setter(node):
            return []

        type_ = "method"
        properties = []

        if node.type == "function":
            type_ = "function"

            if isinstance(node, astroid.AsyncFunctionDef):
                properties.append("async")
        elif _astroid_utils.is_decorated_with_property(node):
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
            "args": _astroid_utils.get_args_info(node.args),
            "doc": _prepare_docstring(node.doc_node.value if node.doc_node else ""),
            "from_line_no": node.fromlineno,
            "to_line_no": node.tolineno,
            "return_annotation": _astroid_utils.get_return_annotation(node),
            "properties": properties,
            "is_overload": _astroid_utils.is_decorated_with_overload(node),
            "overloads": [],
        }

        result = [data]

        if node.name == "__init__":
            for child in node.get_children():
                if isinstance(child, (astroid.nodes.Assign, astroid.nodes.AnnAssign)):
                    # Verify we are assigning to self.
                    if isinstance(child, astroid.nodes.Assign):
                        targets = child.targets
                    else:
                        targets = [child.target]

                    target_ok = True
                    for target in targets:
                        if not isinstance(target, astroid.nodes.AssignAttr):
                            target_ok = False
                            break
                        _object = target.expr
                        if (
                            not isinstance(_object, astroid.nodes.Name)
                            or _object.name != "self"
                        ):
                            target_ok = False
                            break
                    if not target_ok:
                        continue
                    child_data = self._parse_assign(child)
                    result.extend(data for data in child_data)

        return result

    def _parse_local_import_from(self, node):
        result = []

        for import_name, alias in node.names:
            is_wildcard = (alias or import_name) == "*"
            original_path = _astroid_utils.get_full_import_name(
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
            "all": _astroid_utils.get_module_all(node),
        }

        overloads = {}
        top_name = node.name.split(".", 1)[0]
        for child in node.get_children():
            if _astroid_utils.is_local_import_from(child, top_name):
                children_data = self._parse_local_import_from(child)
            else:
                children_data = self.parse(child)

            for child_data in children_data:
                if _parse_child(child_data, overloads):
                    data["children"].append(child_data)

        return data

    def parse_typealias(self, node):
        doc = ""
        doc_node = node.next_sibling()
        if isinstance(doc_node, astroid.nodes.Expr) and isinstance(
            doc_node.value, astroid.nodes.Const
        ):
            doc = doc_node.value.value

        if isinstance(node.name, astroid.nodes.AssignName):
            name = node.name.name
        elif isinstance(node.name, astroid.nodes.AssignAttr):
            name = node.name.attrname
        else:
            return []

        data = {
            "type": "data",
            "name": name,
            "qual_name": self._get_qual_name(name),
            "full_name": self._get_full_name(name),
            "doc": _prepare_docstring(doc),
            "value": node.value.as_string(),
            "from_line_no": node.fromlineno,
            "to_line_no": node.tolineno,
            "annotation": "TypeAlias",
        }

        return [data]

    def parse(self, node):
        data = []

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


def _parse_child(child_data, overloads) -> bool:
    if child_data["type"] in ("function", "method", "property"):
        name = child_data["name"]
        if name in overloads:
            grouped = overloads[name]
            grouped["doc"] = child_data["doc"]

            if child_data["is_overload"]:
                grouped["overloads"].append(
                    (child_data["args"], child_data["return_annotation"])
                )

            return False

        if child_data["is_overload"] and name not in overloads:
            overloads[name] = child_data

    return True
