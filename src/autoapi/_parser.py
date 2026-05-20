from __future__ import annotations

from collections.abc import Iterable
from typing import NotRequired, TypedDict

import griffe
import sphinx.util.docstrings
import sphinx.util.logging

from . import _griffe_utils

LOGGER = sphinx.util.logging.getLogger(__name__)


class BaseParsedObject(TypedDict):
    type: str
    name: str
    qual_name: str
    full_name: str
    doc: str


class ParsedAttribute(BaseParsedObject):
    value: str | None
    from_line_no: int
    to_line_no: int
    annotation: str | None


class ParsedClass(BaseParsedObject):
    bases: list[str]
    from_line_no: int
    to_line_no: int
    children: list[dict]
    is_abstract: bool


class ParsedFunction(BaseParsedObject):
    args: list[_griffe_utils.ArgInfo]
    type_params: list[_griffe_utils.TypeParamInfo]
    from_line_no: int
    to_line_no: int
    return_annotation: str
    properties: list[str]
    is_overload: bool
    overloads: list[ParsedFunction]
    inherited: NotRequired[bool]


class ParsedModule(BaseParsedObject):
    children: list[ParsedAttribute | ParsedClass | ParsedFunction | ParsedTypeAlias]
    file_path: str
    all: list[str]


class ParsedTypeAlias(BaseParsedObject):
    value: str
    from_line_no: int
    to_line_no: int
    annotation: str


def _prepare_docstring(doc):
    return "\n".join(sphinx.util.docstrings.prepare_docstring(doc))


class Parser:
    def __init__(self, loader: griffe.GriffeLoader):
        self._loader = loader

    def parse_attribute(self, obj: griffe.Attribute) -> list[ParsedAttribute]:
        type_ = "data"
        if isinstance(obj.parent, griffe.Class):
            type_ = "attribute"

        data = ParsedAttribute({
            "type": type_,
            "name": obj.name,
            "qual_name": obj.path.removeprefix(f"{obj.module.name}."),
            "full_name": obj.path,
            "doc": _prepare_docstring(obj.docstring.value if obj.docstring else ""),
            "value": obj.value,
            "from_line_no": obj.lineno,
            "to_line_no": obj.endlineno,
            "annotation": obj.annotation,
        })

        return [data]

    def parse_class(self, obj: griffe.Class) -> list[ParsedClass]:
        type_ = "class"
        if _griffe_utils.is_exception(obj):
            type_ = "exception"

        data = ParsedClass({
            "type": type_,
            "name": obj.name,
            "qual_name": obj.path.removeprefix(f"{obj.module.name}."),
            "full_name": obj.path,
            "doc": obj.docstring.value if obj.docstring else "",
            "bases": _griffe_utils.relevant_bases(obj),
            "from_line_no": obj.lineno,
            "to_line_no": obj.endlineno,
            "children": [],
            "is_abstract": _griffe_utils.is_abstract(obj),
        })

        for member in obj.members.values():
            if isinstance(member, griffe.Alias):
                try:
                    member = member.final_target
                except (griffe.AliasResolutionError, griffe.CyclicAliasError) as exc:
                    msg = f"Cannot resolve import of {member.target_path} in {obj.path}"
                    LOGGER.warning(msg, type="autoapi", subtype="python_import_resolution")
                    continue

            for child_data in self.parse(member):
                data["children"].append(child_data)

        for member in obj.inherited_members:
            if isinstance(member, griffe.Alias):
                try:
                    member = member.final_target
                except (griffe.AliasResolutionError, griffe.CyclicAliasError) as exc:
                    msg = f"Cannot resolve import of {member.target_path} in {obj.path}"
                    LOGGER.warning(msg, type="autoapi", subtype="python_import_resolution")
                    continue

            for child_data in self.parse(member):
                child_data["inherited"] = True
                # TODO: How to set inherited_from?
                # TODO: Is name and qual_name correct for inherited members?
                # Do we need to use canonical_path?
                # TODO: Check an attribute on a base gets overridden by a property?
                data["children"].append(child_data)

        return [data]

    def parse_function(self, obj: griffe.Function) -> list[ParsedFunction]:
        type_ = "method"
        if isinstance(obj.parent, griffe.Module):
            type_ = "function"
        elif "property" in obj.labels:
            type_ = "property"

        properties = []
        # "__new__" method is implicit classmethod
        if obj.name != "__new__" and "classmethod" in obj.labels:
            properties.append("classmethod")

        for property_type in ("staticmethod", "abstractmethod", "async"):
            if property_type in obj.labels:
                properties.append(property_type)

        data = ParsedFunction({
            "type": type_,
            "name": obj.name,
            "qual_name": obj.path.removeprefix(f"{obj.module.name}."),
            "full_name": obj.path,
            "doc": obj.docstring.value if obj.docstring else "",
            "args": _griffe_utils.get_args_info(obj.parameters),
            "type_params": _griffe_utils.get_type_params_info(obj.type_parameters),
            "from_line_no": obj.lineno,
            "to_line_no": obj.endlineno,
            "return_annotation": obj.returns,
            "properties": properties,
            "is_overload": False,
            "overloads": [],
        })

        for overload in obj.overloads:
            overload_data = self.parse_function(overload)[0]
            overload_data["is_overload"] = True
            data["overloads"].append(overload_data)

        # TODO: Check that attributes created in __init__ are documented.

        return [data]

    def parse_module(self, obj: griffe.Module) -> ParsedModule:
        type_ = "module"
        if obj.is_package or obj.is_subpackage:
            type_ = "package"

        self._loader.expand_exports(obj)

        # TODO: What are the repercussions of the removal of "encoding" from this dict
        data = ParsedModule({
            "type": type_,
            "name": obj.path,
            "qual_name": obj.path,
            "full_name": obj.path,
            "doc": obj.docstring.value if obj.docstring else "",
            "children": [],
            "file_path": obj.filepath,  # TODO: What if this is a list[str]?
            "all": obj.exports,  # TODO: What about items that are ExprName?
        })

        for child in obj.members:
            if isinstance(child, griffe.Alias):
                try:
                    child = child.final_target
                except (griffe.AliasResolutionError, griffe.CyclicAliasError) as exc:
                    msg = f"Cannot resolve import of {child.target_path} in {obj.path}"
                    LOGGER.warning(msg, type="autoapi", subtype="python_import_resolution")
            elif isinstance(child, griffe.Module):
                continue

            for child_data in self.parse(child):
                data["children"].append(child_data)

        return data

    def parse_typealias(self, obj: griffe.TypeAlias) -> list[ParsedTypeAlias]:
        type_ = "data"
        if isinstance(obj.parent, griffe.ClassDef):
            type_ = "attribute"

        data = ParsedTypeAlias({
            "type": type_,
            "name": obj.name,
            "qual_name": obj.path.removeprefix(f"{obj.module.name}."),
            "full_name": obj.path,
            "doc": obj.docstring.value if obj.docstring else "",
            "value": obj.value,  # TODO: What if this is an Expr?
            "from_line_no": obj.lineno,
            "to_line_no": obj.endlineno,
            "annotation": "TypeAlias",
        })

        return [data]

    def parse(self, obj: griffe.Object | griffe.Alias) -> list[dict]:
        if isinstance(obj, griffe.Alias):
            try:
                obj.resolve_target()
            except (griffe.AliasResolutionError, griffe.CyclicAliasError) as exc:
                LOGGER.warning(str(exc), type="autoapi", subtype="python_import_resolution")
                return []

        node_type = obj.kind.value
        parse_func = getattr(self, "parse_" + node_type)
        data = parse_func(obj)

        if isinstance(obj, griffe.Alias):
            data["original_path"] = obj.target_path

        return data

    def parse_many(self, modules: Iterable[griffe.Module]) -> dict[str, ParsedModule]:
        return {module.filepath: self.parse_module(module) for module in modules}
