from __future__ import annotations

import builtins
from collections.abc import Iterable
import itertools
import re
import sys
from typing import Any, NamedTuple

import astroid
import astroid.nodes


if sys.version_info < (3, 10):  # PY310
    from stdlib_list import in_stdlib
else:

    def in_stdlib(module_name: str) -> bool:
        return module_name in sys.stdlib_module_names


class ArgInfo(NamedTuple):
    prefix: str | None
    name: str | None
    annotation: str | None
    default_value: str | None


def resolve_import_alias(
    name: str, import_names: Iterable[tuple[str, str | None]]
) -> str:
    """Resolve a name from an aliased import to its original name.

    Args:
        name: The potentially aliased name to resolve.
        import_names: The pairs of original names and aliases from the import.

    Returns:
        The original name.
    """
    resolved_name = name

    for import_name, imported_as in import_names:
        if import_name == name:
            break
        if imported_as == name:
            resolved_name = import_name
            break

    return resolved_name


def get_full_import_name(import_from: astroid.nodes.ImportFrom, name: str) -> str:
    """Get the full path of a name from a ``from x import y`` statement.

    Args:
        import_from: The astroid node to resolve the name of.
        name: The short name or alias of what was imported.
            This is ``y`` in ``from x import y``
            and ``z`` in ``from x import y as z``.

    Returns:
        str: The full import path of the name.
    """
    partial_basename = resolve_import_alias(name, import_from.names)

    module_name = import_from.modname
    if import_from.level:
        module = import_from.root()
        assert isinstance(module, astroid.nodes.Module)
        module_name = module.relative_to_absolute_name(
            import_from.modname, level=import_from.level
        )

    return f"{module_name}.{partial_basename}"


def resolve_qualname(node: astroid.nodes.NodeNG, basename: str) -> str:
    """Resolve where a node is defined to get its fully qualified name.

    Args:
        node: The node representing the base name.
        basename: The partial base name to resolve.

    Returns:
        The fully resolved base name.
    """
    full_basename = basename

    top_level_name = re.sub(r"\(.*\)", "", basename).split(".", 1)[0]
    if isinstance(node, astroid.nodes.LocalsDictNodeNG):
        lookup_node = node
    else:
        lookup_node = node.scope()

    assigns = lookup_node.lookup(top_level_name)[1]

    for assignment in assigns:
        if isinstance(assignment, astroid.nodes.ImportFrom):
            import_name = get_full_import_name(assignment, top_level_name)
            full_basename = basename.replace(top_level_name, import_name, 1)
            break
        if isinstance(assignment, astroid.nodes.Import):
            import_name = resolve_import_alias(top_level_name, assignment.names)
            full_basename = basename.replace(top_level_name, import_name, 1)
            break
        if isinstance(assignment, astroid.nodes.ClassDef):
            full_basename = assignment.qname()
            break
        if isinstance(assignment, astroid.nodes.AssignName):
            full_basename = f"{assignment.scope().qname()}.{assignment.name}"

    if isinstance(node, astroid.nodes.Call):
        full_basename = re.sub(r"\(.*\)", "()", full_basename)

    if full_basename.startswith("builtins."):
        return full_basename[len("builtins.") :]

    if full_basename.startswith("__builtin__."):
        return full_basename[len("__builtin__.") :]

    return full_basename


def get_full_basenames(node: astroid.nodes.ClassDef) -> Iterable[str]:
    """Resolve the partial names of a class' bases to fully qualified names.

    Args:
        node: The class definition node to resolve the bases of.

    Returns:
        The fully qualified names.
    """
    for base in node.bases:
        yield _resolve_annotation(base)


def _get_const_value(node: astroid.nodes.NodeNG) -> str | None:
    if isinstance(node, astroid.nodes.Const):
        if isinstance(node.value, str) and "\n" in node.value:
            return f'"""{node.value}"""'

    class NotConstException(Exception):
        pass

    def _inner(node: astroid.nodes.NodeNG) -> Any:
        if isinstance(node, (astroid.nodes.List, astroid.nodes.Tuple)):
            new_value = []
            for element in node.elts:
                new_value.append(_inner(element))

            if isinstance(node, astroid.nodes.Tuple):
                return tuple(new_value)

            return new_value
        elif isinstance(node, astroid.nodes.Const):
            # Don't allow multi-line strings inside a data structure.
            if isinstance(node.value, str) and "\n" in node.value:
                raise NotConstException()

            return node.value

        raise NotConstException()

    try:
        result = _inner(node)
    except NotConstException:
        return None

    return repr(result)


def get_assign_value(
    node: astroid.nodes.Assign | astroid.nodes.AnnAssign,
) -> tuple[str, str | None] | None:
    """Get the name and value of the assignment of the given node.

    Assignments to multiple names are ignored, as per PEP 257.

    Args:
        node: The node to get the assignment value from.

    Returns:
        The name that is assigned to, and the string representation of
        the value assigned to the name (if it can be converted).
    """
    try:
        targets = node.targets
    except AttributeError:
        targets = [node.target]

    if len(targets) == 1:
        target = targets[0]
        if isinstance(target, astroid.nodes.AssignName):
            name = target.name
        elif isinstance(target, astroid.nodes.AssignAttr):
            name = target.attrname
        else:
            return None
        return (name, _get_const_value(node.value))

    return None


def get_assign_annotation(
    node: astroid.nodes.Assign | astroid.nodes.AnnAssign,
) -> str | None:
    """Get the type annotation of the assignment of the given node.

    Args:
        node: The node to get the annotation for.

    Returns:
        The type annotation as a string, or None if one does not exist.
    """
    annotation_node = None
    try:
        annotation_node = node.annotation
    except AttributeError:
        annotation_node = node.type_annotation

    return format_annotation(annotation_node)


def is_decorated_with_property(node: astroid.nodes.FunctionDef) -> bool:
    """Check if the function is decorated as a property.

    Args:
        node: The node to check.

    Returns:
        True if the function is a property, False otherwise.
    """
    if not node.decorators:
        return False

    for decorator in node.decorators.nodes:
        if not isinstance(decorator, astroid.nodes.Name):
            continue

        try:
            if _is_property_decorator(decorator):
                return True
        except astroid.InferenceError:
            pass

    return False


def _is_property_decorator(decorator: astroid.nodes.Name) -> bool:
    def _is_property_class(class_node: astroid.nodes.ClassDef) -> bool:
        return (
            class_node.name == "property"
            and class_node.root().name == builtins.__name__
        ) or (
            class_node.name == "cached_property"
            and class_node.root().name == "functools"
        )

    for inferred in decorator.infer():
        if not isinstance(inferred, astroid.nodes.ClassDef):
            continue

        if _is_property_class(inferred):
            return True

        if any(_is_property_class(ancestor) for ancestor in inferred.ancestors()):
            return True

    return False


def is_decorated_with_property_setter(node: astroid.nodes.FunctionDef) -> bool:
    """Check if the function is decorated as a property setter.

    Args:
        node: The node to check.

    Returns:
        True if the function is a property setter, False otherwise.
    """
    if not node.decorators:
        return False

    for decorator in node.decorators.nodes:
        if (
            isinstance(decorator, astroid.nodes.Attribute)
            and decorator.attrname == "setter"
        ):
            return True

    return False


def is_decorated_with_overload(node: astroid.nodes.FunctionDef) -> bool:
    """Check if the function is decorated as an overload definition.

    Args:
        node: The node to check.

    Returns:
        True if the function is an overload definition, False otherwise.
    """
    if not node.decorators:
        return False

    for decorator in node.decorators.nodes:
        if not isinstance(decorator, (astroid.nodes.Name, astroid.nodes.Attribute)):
            continue

        try:
            if _is_overload_decorator(decorator):
                return True
        except astroid.InferenceError:
            pass

    return False


def _is_overload_decorator(
    decorator: astroid.nodes.Name | astroid.nodes.Attribute,
) -> bool:
    for inferred in decorator.infer():
        if not isinstance(inferred, astroid.nodes.FunctionDef):
            continue

        if inferred.name == "overload" and inferred.root().name == "typing":
            return True

    return False


def is_constructor(node: astroid.nodes.FunctionDef) -> bool:
    """Check if the function is a constructor.

    Args:
        node: The node to check.

    Returns:
        True if the function is a constructor, False otherwise.
    """
    return (
        node.parent
        and isinstance(node.parent.scope(), astroid.nodes.ClassDef)
        and node.name == "__init__"
    )


def is_exception(node: astroid.nodes.ClassDef) -> bool:
    """Check if a class is an exception.

    Args:
        node: The node to check.

    Returns:
        True if the class is an exception, False otherwise.
    """
    if node.name in ("Exception", "BaseException") and node.root().name == "builtins":
        return True

    if not hasattr(node, "ancestors"):
        return False

    return any(is_exception(parent) for parent in node.ancestors(recurs=True))


def is_local_import_from(node: astroid.nodes.NodeNG, package_name: str) -> bool:
    """Check if a node is an import from the local package.

    Args:
        node: The node to check.
        package_name: The name of the local package.

    Returns:
        True if the node is an import from the local package. False otherwise.
    """
    if not isinstance(node, astroid.nodes.ImportFrom):
        return False

    return (
        node.level
        or node.modname == package_name
        or node.modname.startswith(package_name + ".")
    )


def get_module_all(node: astroid.nodes.Module) -> list[str] | None:
    """Get the contents of the ``__all__`` variable from a module.

    Args:
        node: The module to get ``__all__`` from.

    Returns:
        The contents of ``__all__`` if defined. Otherwise ``None``.
    """
    all_ = None

    if "__all__" in node.locals:
        assigned = next(node.igetattr("__all__"))
        if assigned is not astroid.Uninferable:
            all_ = []
            for elt in getattr(assigned, "elts", ()):
                try:
                    elt_name = next(elt.infer())
                except astroid.InferenceError:
                    continue

                if elt_name is astroid.Uninferable:
                    continue

                if isinstance(elt_name, astroid.nodes.Const) and isinstance(
                    elt_name.value, str
                ):
                    all_.append(elt_name.value)

    return all_


def _is_ellipsis(node: astroid.nodes.NodeNG) -> bool:
    return isinstance(node, astroid.nodes.Const) and node.value == Ellipsis


def merge_annotations(
    annotations: Iterable[astroid.nodes.NodeNG],
    comment_annotations: Iterable[astroid.nodes.NodeNG],
) -> Iterable[astroid.nodes.NodeNG | None]:
    for ann, comment_ann in itertools.zip_longest(annotations, comment_annotations):
        if ann and not _is_ellipsis(ann):
            yield ann
        elif comment_ann and not _is_ellipsis(comment_ann):
            yield comment_ann
        else:
            yield None


def _resolve_annotation(annotation: astroid.nodes.NodeNG) -> str:
    resolved: str

    if isinstance(annotation, astroid.nodes.Const):
        resolved = resolve_qualname(annotation, str(annotation.value))
    elif isinstance(annotation, astroid.nodes.Name):
        resolved = resolve_qualname(annotation, annotation.name)
    elif isinstance(annotation, astroid.nodes.Attribute):
        resolved = resolve_qualname(annotation, annotation.as_string())
    elif isinstance(annotation, astroid.nodes.Subscript):
        value = _resolve_annotation(annotation.value)
        slice_node = annotation.slice
        # astroid.Index was removed in astroid v3
        if hasattr(astroid.nodes, "Index") and isinstance(
            slice_node, astroid.nodes.Index
        ):
            slice_node = slice_node.value
        if value == "Literal":
            if isinstance(slice_node, astroid.nodes.Tuple):
                elts = slice_node.elts
            else:
                elts = [slice_node]
            slice_ = ", ".join(
                (
                    elt.as_string()
                    if isinstance(elt, astroid.nodes.Const)
                    else _resolve_annotation(elt)
                )
                for elt in elts
            )
        elif isinstance(slice_node, astroid.nodes.Tuple):
            slice_ = ", ".join(_resolve_annotation(elt) for elt in slice_node.elts)
        else:
            slice_ = _resolve_annotation(slice_node)
        resolved = f"{value}[{slice_}]"
    elif isinstance(annotation, astroid.nodes.Tuple):
        resolved = (
            "(" + ", ".join(_resolve_annotation(elt) for elt in annotation.elts) + ")"
        )
    elif isinstance(annotation, astroid.nodes.List):
        resolved = (
            "[" + ", ".join(_resolve_annotation(elt) for elt in annotation.elts) + "]"
        )
    elif isinstance(annotation, astroid.nodes.BinOp) and annotation.op == "|":
        left = _resolve_annotation(annotation.left)
        right = _resolve_annotation(annotation.right)
        resolved = f"{left} | {right}"
    else:
        resolved = annotation.as_string()

    if resolved.startswith("typing."):
        return resolved[len("typing.") :]

    # Sphinx is capable of linking anything in the same module
    # without needing a fully qualified path.
    module_prefix = annotation.root().name + "."
    if resolved.startswith(module_prefix):
        return resolved[len(module_prefix) :]

    return resolved


def format_annotation(annotation: astroid.nodes.NodeNG | None) -> str | None:
    if annotation:
        return _resolve_annotation(annotation)

    return annotation


def _iter_args(
    args: list[astroid.nodes.AssignName],
    annotations: list[astroid.nodes.NodeNG | None],
    defaults: list[astroid.nodes.NodeNG],
) -> Iterable[tuple[str, str | None, str | None]]:
    default_offset = len(args) - len(defaults)
    packed = itertools.zip_longest(args, annotations)
    for i, (arg, annotation) in enumerate(packed):
        default = None
        if defaults is not None and i >= default_offset:
            if defaults[i - default_offset] is not None:
                default = defaults[i - default_offset].as_string()

        name = arg.name
        if isinstance(arg, astroid.nodes.Tuple):
            argument_names = ", ".join(x.name for x in arg.elts)
            name = f"({argument_names})"

        yield (name, format_annotation(annotation), default)


def get_args_info(args_node: astroid.nodes.Arguments) -> list[ArgInfo]:
    result: list[ArgInfo] = []
    positional_only_defaults = []
    positional_or_keyword_defaults = args_node.defaults
    if args_node.defaults:
        args = args_node.args or []
        positional_or_keyword_defaults = args_node.defaults[-len(args) :]
        positional_only_defaults = args_node.defaults[
            : len(args_node.defaults) - len(args)
        ]

    plain_annotations = args_node.annotations or ()

    func_comment_annotations = args_node.parent.type_comment_args or []
    if args_node.parent.type in ("method", "classmethod"):
        func_comment_annotations = [None] + func_comment_annotations

    comment_annotations = args_node.type_comment_posonlyargs
    comment_annotations += args_node.type_comment_args or []
    comment_annotations += args_node.type_comment_kwonlyargs
    annotations = list(
        merge_annotations(
            plain_annotations,
            merge_annotations(func_comment_annotations, comment_annotations),
        )
    )
    annotation_offset = 0

    if args_node.posonlyargs:
        posonlyargs_annotations = args_node.posonlyargs_annotations
        if not any(args_node.posonlyargs_annotations):
            num_args = len(args_node.posonlyargs)
            posonlyargs_annotations = annotations[
                annotation_offset : annotation_offset + num_args
            ]

        for arg, annotation, default in _iter_args(
            args_node.posonlyargs, posonlyargs_annotations, positional_only_defaults
        ):
            result.append(ArgInfo(None, arg, annotation, default))

        result.append(ArgInfo("/", None, None, None))

        if not any(args_node.posonlyargs_annotations):
            annotation_offset += num_args

    if args_node.args:
        num_args = len(args_node.args)
        for arg, annotation, default in _iter_args(
            args_node.args,
            annotations[annotation_offset : annotation_offset + num_args],
            positional_or_keyword_defaults,
        ):
            result.append(ArgInfo(None, arg, annotation, default))

        annotation_offset += num_args

    if args_node.vararg:
        annotation = None
        if args_node.varargannotation:
            annotation = format_annotation(args_node.varargannotation)
        elif len(annotations) > annotation_offset and annotations[annotation_offset]:
            annotation = format_annotation(annotations[annotation_offset])
            annotation_offset += 1
        result.append(ArgInfo("*", args_node.vararg, annotation, None))

    if args_node.kwonlyargs:
        if not args_node.vararg:
            result.append(ArgInfo("*", None, None, None))

        kwonlyargs_annotations = args_node.kwonlyargs_annotations
        if not any(args_node.kwonlyargs_annotations):
            num_args = len(args_node.kwonlyargs)
            kwonlyargs_annotations = annotations[
                annotation_offset : annotation_offset + num_args
            ]

        for arg, annotation, default in _iter_args(
            args_node.kwonlyargs,
            kwonlyargs_annotations,
            args_node.kw_defaults,
        ):
            result.append(ArgInfo(None, arg, annotation, default))

        if not any(args_node.kwonlyargs_annotations):
            annotation_offset += num_args

    if args_node.kwarg:
        annotation = None
        if args_node.kwargannotation:
            annotation = format_annotation(args_node.kwargannotation)
        elif len(annotations) > annotation_offset and annotations[annotation_offset]:
            annotation = format_annotation(annotations[annotation_offset])
            annotation_offset += 1
        result.append(ArgInfo("**", args_node.kwarg, annotation, None))

    if args_node.parent.type in ("method", "classmethod") and result:
        result.pop(0)

    return result


def get_return_annotation(node: astroid.nodes.FunctionDef) -> str | None:
    """Get the return annotation of a node.

    Args:
        node: The node to get the return annotation for.

    Returns:
        The return annotation of the given node.
    """
    return_annotation = None

    if node.returns:
        return_annotation = format_annotation(node.returns)
    elif node.type_comment_returns:
        return_annotation = format_annotation(node.type_comment_returns)

    return return_annotation


def get_class_docstring(node: astroid.nodes.ClassDef) -> str:
    """Get the docstring of a node, using a parent docstring if needed.

    Args:
        node: The node to get a docstring for.

    Returns:
        The docstring of the class, or the empty string if no docstring
        was found or defined.
    """
    doc = node.doc_node.value if node.doc_node else ""

    if not doc:
        for base in node.ancestors():
            if base.qname() in (
                "__builtins__.object",
                "builtins.object",
                "builtins.type",
            ):
                continue
            if base.doc_node is not None:
                return base.doc_node.value

    return doc


def is_abstract_class(node: astroid.nodes.ClassDef) -> bool:
    metaclass = node.metaclass()
    if metaclass and metaclass.name == "ABCMeta":
        return True

    if "abc.ABC" in node.basenames:
        return True

    if any(method.is_abstract(pass_is_abstract=False) for method in node.methods()):
        return True

    return False
