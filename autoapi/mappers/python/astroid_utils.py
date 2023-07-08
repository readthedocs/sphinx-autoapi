import builtins
import itertools
import re

import astroid
import astroid.nodes

import astroid.nodes.node_classes
import sphinx.util.logging

_LOGGER = sphinx.util.logging.getLogger(__name__)


def resolve_import_alias(name, import_names):
    """Resolve a name from an aliased import to its original name.

    :param name: The potentially aliased name to resolve.
    :type name: str
    :param import_names: The pairs of original names and aliases
        from the import.
    :type import_names: iterable(tuple(str, str or None))

    :returns: The original name.
    :rtype: str
    """
    resolved_name = name

    for import_name, imported_as in import_names:
        if import_name == name:
            break
        if imported_as == name:
            resolved_name = import_name
            break

    return resolved_name


def get_full_import_name(import_from, name):
    """Get the full path of a name from a ``from x import y`` statement.

    Args:
        import_from (astroid.nodes.ImportFrom): The astroid node to
            resolve the name of.
        name (str)

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


def resolve_qualname(node, basename):
    """Resolve where a node is defined to get its fully qualified name.

    Args:
        node (astroid.NodeNG): The node representing the base name.
        basename (str): The partial base name to resolve.

    Returns:
        str: The fully resolved base name.
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


def get_full_basenames(node):
    """Resolve the partial names of a class' bases to fully qualified names.

    Args:
        node: The class definition node to resolve the bases of.
    :type: astroid.ClassDef

    Returns:
        iterable(str): The full names.
    """
    for base in node.bases:
        yield _resolve_annotation(base)


def _get_const_values(node):
    value = None

    if isinstance(node, (astroid.nodes.List, astroid.nodes.Tuple)):
        new_value = []
        for element in node.elts:
            if isinstance(element, astroid.nodes.Const):
                new_value.append(element.value)
            elif isinstance(element, (astroid.nodes.List, astroid.nodes.Tuple)):
                new_value.append(_get_const_values(element))
            else:
                break
        else:
            value = new_value

        if isinstance(node, astroid.nodes.Tuple):
            value = tuple(new_value)
    elif isinstance(node, astroid.nodes.Const):
        value = node.value

    return value


def get_assign_value(node):
    """Get the name and value of the assignment of the given node.

    Assignments to multiple names are ignored, as per PEP 257.

    Args:
        node (astroid.nodes.Assign or astroid.nodes.AnnAssign): The node
            to get the assignment value from.

    Returns:
        tuple(str, object or None) or None: The name that is assigned
        to, and the value assigned to the name (if it can be converted).
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
        return (name, _get_const_values(node.value))

    return None


def get_assign_annotation(node):
    """Get the type annotation of the assignment of the given node.

    Args:
        node (astroid.nodes.Assign or astroid.nodes.AnnAssign): The node
            to get the annotation for.

    Returns:
        str or None: The type annotation as a string, or None if one
        does not exist.
    """
    annotation_node = None
    try:
        annotation_node = node.annotation
    except AttributeError:
        annotation_node = node.type_annotation

    return format_annotation(annotation_node)


def is_decorated_with_property(node):
    """Check if the function is decorated as a property.

    Args:
        node (astroid.nodes.FunctionDef): The node to check.

    Returns:
        bool: True if the function is a property, False otherwise.
    """
    if not node.decorators:
        return False

    for decorator in node.decorators.nodes:
        if not isinstance(decorator, astroid.Name):
            continue

        try:
            if _is_property_decorator(decorator):
                return True
        except astroid.InferenceError:
            pass

    return False


def _is_property_decorator(decorator):
    def _is_property_class(class_node):
        return (
            class_node.name == "property"
            and class_node.root().name == builtins.__name__
        )

    for inferred in decorator.infer():
        if not isinstance(inferred, astroid.nodes.ClassDef):
            continue

        if _is_property_class(inferred):
            return True

        if any(_is_property_class(ancestor) for ancestor in inferred.ancestors()):
            return True

    return False


def is_decorated_with_property_setter(node):
    """Check if the function is decorated as a property setter.

    Args:
        node (astroid.nodes.FunctionDef): The node to check.

    Returns:
        bool: True if the function is a property setter, False
        otherwise.
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


def is_decorated_with_overload(node):
    """Check if the function is decorated as an overload definition.

    Args:
        node (astroid.nodes.FunctionDef): The node to check.

    Returns:
        bool: True if the function is an overload definition, False
        otherwise.
    """
    if not node.decorators:
        return False

    for decorator in node.decorators.nodes:
        if not isinstance(decorator, (astroid.Name, astroid.Attribute)):
            continue

        try:
            if _is_overload_decorator(decorator):
                return True
        except astroid.InferenceError:
            pass

    return False


def _is_overload_decorator(decorator):
    for inferred in decorator.infer():
        if not isinstance(inferred, astroid.nodes.FunctionDef):
            continue

        if inferred.name == "overload" and inferred.root().name == "typing":
            return True

    return False


def is_constructor(node):
    """Check if the function is a constructor.

    Args:
        node (astroid.nodes.FunctionDef): The node to check.

    Returns:
        bool: True if the function is a constructor, False otherwise.
    """
    return (
        node.parent
        and isinstance(node.parent.scope(), astroid.nodes.ClassDef)
        and node.name == "__init__"
    )


def is_exception(node):
    """Check if a class is an exception.

    Args:
        node (astroid.nodes.ClassDef): The node to check.

    Returns:
        bool: True if the class is an exception, False otherwise.
    """
    if node.name in ("Exception", "BaseException") and node.root().name == "builtins":
        return True

    if not hasattr(node, "ancestors"):
        return False

    return any(is_exception(parent) for parent in node.ancestors(recurs=True))


def is_local_import_from(node, package_name):
    """Check if a node is an import from the local package.

    Args:
        node (astroid.node.NodeNG): The node to check.
        package_name (str): The name of the local package.

    Returns:
        bool: True if the node is an import from the local package,
        False otherwise.
    """
    if not isinstance(node, astroid.ImportFrom):
        return False

    return (
        node.level
        or node.modname == package_name
        or node.modname.startswith(package_name + ".")
    )


def get_module_all(node):
    """Get the contents of the ``__all__`` variable from a module.

    Args:
        node (astroid.nodes.Module): The module to get ``__all__`` from.

    Returns:
        list(str) or None: The contents of ``__all__`` if defined.
        Otherwise None.
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

                if isinstance(elt_name, astroid.Const) and isinstance(
                    elt_name.value, str
                ):
                    all_.append(elt_name.value)

    return all_


def _is_ellipsis(node):
    return isinstance(node, astroid.Const) and node.value == Ellipsis


def merge_annotations(annotations, comment_annotations):
    for ann, comment_ann in itertools.zip_longest(annotations, comment_annotations):
        if ann and not _is_ellipsis(ann):
            yield ann
        elif comment_ann and not _is_ellipsis(comment_ann):
            yield comment_ann
        else:
            yield None


def _resolve_annotation(annotation):
    resolved = None

    if isinstance(annotation, astroid.Const):
        resolved = resolve_qualname(annotation, str(annotation.value))
    elif isinstance(annotation, astroid.Name):
        resolved = resolve_qualname(annotation, annotation.name)
    elif isinstance(annotation, astroid.Attribute):
        resolved = resolve_qualname(annotation, annotation.as_string())
    elif isinstance(annotation, astroid.Subscript):
        value = _resolve_annotation(annotation.value)
        slice_node = annotation.slice
        # astroid.Index was removed in astroid v3
        if hasattr(astroid, "Index") and isinstance(slice_node, astroid.Index):
            slice_node = slice_node.value
        if isinstance(slice_node, astroid.Tuple):
            slice_ = ", ".join(_resolve_annotation(elt) for elt in slice_node.elts)
        else:
            slice_ = _resolve_annotation(slice_node)
        resolved = f"{value}[{slice_}]"
    elif isinstance(annotation, astroid.Tuple):
        resolved = (
            "(" + ", ".join(_resolve_annotation(elt) for elt in annotation.elts) + ")"
        )
    elif isinstance(annotation, astroid.List):
        resolved = (
            "[" + ", ".join(_resolve_annotation(elt) for elt in annotation.elts) + "]"
        )
    elif isinstance(annotation, astroid.BinOp) and annotation.op == "|":
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


def format_annotation(annotation):
    if annotation:
        return _resolve_annotation(annotation)

    return annotation


def _iter_args(args, annotations, defaults):
    default_offset = len(args) - len(defaults)
    packed = itertools.zip_longest(args, annotations)
    for i, (arg, annotation) in enumerate(packed):
        default = None
        if defaults is not None and i >= default_offset:
            if defaults[i - default_offset] is not None:
                default = defaults[i - default_offset].as_string()

        name = arg.name
        if isinstance(arg, astroid.Tuple):
            argument_names = ", ".join(x.name for x in arg.elts)
            name = f"({argument_names})"

        yield (name, format_annotation(annotation), default)


def get_args_info(args_node):
    result = []
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
            result.append((None, arg, annotation, default))

        result.append(("/", None, None, None))

        if not any(args_node.posonlyargs_annotations):
            annotation_offset += num_args

    if args_node.args:
        num_args = len(args_node.args)
        for arg, annotation, default in _iter_args(
            args_node.args,
            annotations[annotation_offset : annotation_offset + num_args],
            positional_or_keyword_defaults,
        ):
            result.append((None, arg, annotation, default))

        annotation_offset += num_args

    if args_node.vararg:
        annotation = None
        if args_node.varargannotation:
            annotation = format_annotation(args_node.varargannotation)
        elif len(annotations) > annotation_offset and annotations[annotation_offset]:
            annotation = format_annotation(annotations[annotation_offset])
            annotation_offset += 1
        result.append(("*", args_node.vararg, annotation, None))

    if args_node.kwonlyargs:
        if not args_node.vararg:
            result.append(("*", None, None, None))

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
            result.append((None, arg, annotation, default))

        if not any(args_node.kwonlyargs_annotations):
            annotation_offset += num_args

    if args_node.kwarg:
        annotation = None
        if args_node.kwargannotation:
            annotation = format_annotation(args_node.kwargannotation)
        elif len(annotations) > annotation_offset and annotations[annotation_offset]:
            annotation = format_annotation(annotations[annotation_offset])
            annotation_offset += 1
        result.append(("**", args_node.kwarg, annotation, None))

    if args_node.parent.type in ("method", "classmethod") and result:
        result.pop(0)

    return result


def get_return_annotation(node):
    """Get the return annotation of a node.

    Args:
        node (astroid.nodes.FunctionDef)
    """
    return_annotation = None

    if node.returns:
        return_annotation = format_annotation(node.returns)
    elif node.type_comment_returns:
        return_annotation = format_annotation(node.type_comment_returns)

    return return_annotation


def get_func_docstring(node):
    """Get the docstring of a node, using a parent docstring if needed.

    Args:
        node (astroid.nodes.FunctionDef): The node to get a docstring
            for.
    """
    doc = node.doc_node.value if node.doc_node else ""

    if not doc and isinstance(node.parent, astroid.nodes.ClassDef):
        for base in node.parent.ancestors():
            if node.name in ("__init__", "__new__") and base.qname() in (
                "__builtins__.object",
                "builtins.object",
                "builtins.type",
            ):
                continue
            for child in base.get_children():
                if (
                    isinstance(child, node.__class__)
                    and child.name == node.name
                    and child.doc_node is not None
                ):
                    return child.doc_node.value

    return doc


def get_class_docstring(node):
    """Get the docstring of a node, using a parent docstring if needed.

    Args:
        node (astroid.nodes.ClassDef): The node to get a docstring for.
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
