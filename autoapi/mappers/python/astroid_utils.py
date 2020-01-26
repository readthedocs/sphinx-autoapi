try:
    import builtins
except ImportError:
    import __builtin__ as builtins
import itertools
import re
import sys

import astroid
import astroid.nodes
import sphinx.util.logging

_LOGGER = sphinx.util.logging.getLogger(__name__)


if sys.version_info < (3,):
    _EXCEPTIONS_MODULE = "exceptions"
    # getattr to keep linter happy
    _STRING_TYPES = getattr(builtins, "basestring")
    _zip_longest = itertools.izip_longest  # pylint: disable=invalid-name,no-member
else:
    _EXCEPTIONS_MODULE = "builtins"
    _STRING_TYPES = (str,)
    _zip_longest = itertools.zip_longest  # pylint: disable=invalid-name


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

    :param import_from: The astroid node to resolve the name of.
    :type import_from: astroid.nodes.ImportFrom
    :param name:
    :type name: str

    :returns: The full import path of the name.
    :rtype: str
    """
    partial_basename = resolve_import_alias(name, import_from.names)

    module_name = import_from.modname
    if import_from.level:
        module = import_from.root()
        assert isinstance(module, astroid.nodes.Module)
        module_name = module.relative_to_absolute_name(
            import_from.modname, level=import_from.level
        )

    return "{}.{}".format(module_name, partial_basename)


def get_full_basename(node, basename):
    """Resolve a partial base name to the full path.

    :param node: The node representing the base name.
    :type node: astroid.NodeNG
    :param basename: The partial base name to resolve.
    :type basename: str

    :returns: The fully resolved base name.
    :rtype: str
    """
    full_basename = basename

    top_level_name = re.sub(r"\(.*\)", "", basename).split(".", 1)[0]
    lookup_node = node
    while not hasattr(lookup_node, "lookup"):
        lookup_node = lookup_node.parent
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
            full_basename = "{}.{}".format(assignment.root().name, assignment.name)
            break

    if isinstance(node, astroid.nodes.Call):
        full_basename = re.sub(r"\(.*\)", "()", full_basename)

    if full_basename.startswith("builtins."):
        return full_basename[len("builtins.") :]

    if full_basename.startswith("__builtin__."):
        return full_basename[len("__builtin__.") :]

    return full_basename


def get_full_basenames(bases, basenames):
    """Resolve the base nodes and partial names of a class to full names.

    :param bases: The astroid node representing something that a class
        inherits from.
    :type bases: iterable(astroid.NodeNG)
    :param basenames: The partial name of something that a class inherits from.
    :type basenames: iterable(str)

    :returns: The full names.
    :rtype: iterable(str)
    """
    for base, basename in zip(bases, basenames):
        yield get_full_basename(base, basename)


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
    elif isinstance(node, astroid.nodes.Const):
        value = node.value

    return value


def get_assign_value(node):
    """Get the name and value of the assignment of the given node.

    Assignments to multiple names are ignored, as per PEP 257.

    :param node: The node to get the assignment value from.
    :type node: astroid.nodes.Assign or astroid.nodes.AnnAssign

    :returns: The name that is assigned to,
        and the value assigned to the name (if it can be converted).
    :rtype: tuple(str, object or None) or None
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

    :param node: The node to get the annotation for.
    :type node: astroid.nodes.Assign or astroid.nodes.AnnAssign

    :returns: The type annotation as a string, or None if one does not exist.
    :rtype: str or None
    """
    annotation = None

    annotation_node = None
    try:
        annotation_node = node.annotation
    except AttributeError:
        # Python 2 has no support for type annotations, so use getattr
        annotation_node = getattr(node, "type_annotation", None)

    if annotation_node:
        if isinstance(annotation_node, astroid.nodes.Const):
            annotation = node.value
        else:
            annotation = annotation_node.as_string()

    return annotation


def is_decorated_with_property(node):
    """Check if the function is decorated as a property.

    :param node: The node to check.
    :type node: astroid.nodes.FunctionDef

    :returns: True if the function is a property, False otherwise.
    :rtype: bool
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

    :param node: The node to check.
    :type node: astroid.nodes.FunctionDef

    :returns: True if the function is a property setter, False otherwise.
    :rtype: bool
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


def is_constructor(node):
    """Check if the function is a constructor.

    :param node: The node to check.
    :type node: astroid.nodes.FunctionDef

    :returns: True if the function is a constructor, False otherwise.
    :rtype: bool
    """
    return (
        node.parent
        and isinstance(node.parent.scope(), astroid.nodes.ClassDef)
        and node.name == "__init__"
    )


def is_exception(node):
    """Check if a class is an exception.

    :param node: The node to check.
    :type node: astroid.nodes.ClassDef

    :returns: True if the class is an exception, False otherwise.
    :rtype: bool
    """
    if (
        node.name in ("Exception", "BaseException")
        and node.root().name == _EXCEPTIONS_MODULE
    ):
        return True

    if not hasattr(node, "ancestors"):
        return False

    return any(is_exception(parent) for parent in node.ancestors(recurs=True))


def is_local_import_from(node, package_name):
    """Check if a node is an import from the local package.

    :param node: The node to check.
    :type node: astroid.node.NodeNG

    :param package_name: The name of the local package.
    :type package_name: str

    :returns: True if the node is an import from the local package,
        False otherwise.
    :rtype: bool
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

    :param node: The module to get ``__all__`` from.
    :type node: astroid.nodes.Module

    :returns: The contents of ``__all__`` if defined. Otherwise None.
    :rtype: list(str) or None
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
                    elt_name.value, _STRING_TYPES
                ):
                    all_.append(elt_name.value)

    return all_


def _is_ellipsis(node):
    if sys.version_info < (3, 8):
        return isinstance(node, astroid.Ellipsis)

    return isinstance(node, astroid.Const) and node.value == Ellipsis


def merge_annotations(annotations, comment_annotations):
    for ann, comment_ann in _zip_longest(annotations, comment_annotations):
        if ann and not _is_ellipsis(ann):
            yield ann
        elif comment_ann and not _is_ellipsis(comment_ann):
            yield comment_ann
        else:
            yield None


def _format_args(args, defaults=None, annotations=None):
    values = []

    if args is None:
        return ""

    if annotations is None:
        annotations = []

    if defaults is not None:
        default_offset = len(args) - len(defaults)

    packed = _zip_longest(args, annotations)
    for i, (arg, annotation) in enumerate(packed):
        if isinstance(arg, astroid.Tuple):
            values.append("({})".format(_format_args(arg.elts)))
        else:
            argname = arg.name
            default_sep = "="
            if annotation is not None:
                ann_str = annotation.as_string()
                if isinstance(annotation, astroid.Const):
                    ann_str = annotation.value
                argname = "{}: {}".format(argname, ann_str)
                default_sep = " = "
            values.append(argname)

            if defaults is not None and i >= default_offset:
                if defaults[i - default_offset] is not None:
                    values[-1] += default_sep + defaults[i - default_offset].as_string()

    return ", ".join(values)


def format_args(args_node):  # pylint: disable=too-many-branches,too-many-statements
    result = []
    positional_only_defaults = []
    positional_or_keyword_defaults = args_node.defaults
    if args_node.defaults:
        args = args_node.args or []
        positional_or_keyword_defaults = args_node.defaults[-len(args) :]
        positional_only_defaults = args_node.defaults[
            : len(args_node.defaults) - len(args)
        ]

    plain_annotations = getattr(args_node, "annotations", ()) or ()
    func_comment_annotations = getattr(args_node.parent, "type_comment_args", ()) or ()
    comment_annotations = getattr(args_node, "type_comment_args", []) or []
    if hasattr(args_node, "type_comment_posonlyargs"):
        comment_annotations = args_node.type_comment_posonlyargs + comment_annotations
    else:
        # astroid used to not expose type comments of positional only arguments,
        # so pad the comments with the number of positional only arguments.
        comment_annotations = (
            [None] * len(getattr(args_node, "posonlyargs", ()))
        ) + comment_annotations
    if hasattr(args_node, "type_comment_kwonlyargs"):
        comment_annotations += args_node.type_comment_kwonlyargs
    annotations = list(
        merge_annotations(
            plain_annotations,
            merge_annotations(func_comment_annotations, comment_annotations),
        )
    )
    annotation_offset = 0

    if getattr(args_node, "posonlyargs", None):
        posonlyargs_annotations = args_node.posonlyargs_annotations
        if not any(args_node.posonlyargs_annotations):
            num_args = len(args_node.posonlyargs)
            posonlyargs_annotations = annotations[
                annotation_offset : annotation_offset + num_args
            ]

        result.append(
            _format_args(
                args_node.posonlyargs, positional_only_defaults, posonlyargs_annotations
            )
        )
        result.append("/")

        if not any(args_node.posonlyargs_annotations):
            annotation_offset += num_args

    if args_node.args:
        num_args = len(args_node.args)
        result.append(
            _format_args(
                args_node.args,
                positional_or_keyword_defaults,
                annotations[annotation_offset : annotation_offset + num_args],
            )
        )
        annotation_offset += num_args

    if args_node.vararg:
        vararg_result = "*{}".format(args_node.vararg)
        if getattr(args_node, "varargannotation", None):
            vararg_result = "{}: {}".format(
                vararg_result, args_node.varargannotation.as_string()
            )
        elif len(annotations) > annotation_offset and annotations[annotation_offset]:
            vararg_result = "{}: {}".format(
                vararg_result, annotations[annotation_offset].as_string()
            )
            annotation_offset += 1
        result.append(vararg_result)

    if getattr(args_node, "kwonlyargs", None):
        if not args_node.vararg:
            result.append("*")

        kwonlyargs_annotations = args_node.kwonlyargs_annotations
        if not any(args_node.kwonlyargs_annotations):
            num_args = len(args_node.kwonlyargs)
            kwonlyargs_annotations = annotations[
                annotation_offset : annotation_offset + num_args
            ]

        result.append(
            _format_args(
                args_node.kwonlyargs, args_node.kw_defaults, kwonlyargs_annotations,
            )
        )

        if not any(args_node.kwonlyargs_annotations):
            annotation_offset += num_args

    if args_node.kwarg:
        kwarg_result = "**{}".format(args_node.kwarg)
        if getattr(args_node, "kwargannotation", None):
            kwarg_result = "{}: {}".format(
                kwarg_result, args_node.kwargannotation.as_string()
            )
        elif len(annotations) > annotation_offset and annotations[annotation_offset]:
            kwarg_result = "{}: {}".format(
                kwarg_result, annotations[annotation_offset].as_string()
            )
            annotation_offset += 1
        result.append(kwarg_result)

    return ", ".join(result)
