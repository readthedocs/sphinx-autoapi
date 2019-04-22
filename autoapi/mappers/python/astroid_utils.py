try:
    import builtins
except ImportError:
    import __builtin__ as builtins
import re
import sys

import astroid
import astroid.nodes


if sys.version_info < (3,):
    _EXCEPTIONS_MODULE = "exceptions"
    # getattr to keep linter happy
    _STRING_TYPES = getattr(builtins, "basestring")
else:
    _EXCEPTIONS_MODULE = "builtins"
    _STRING_TYPES = str


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
        elif isinstance(assignment, astroid.nodes.Import):
            import_name = resolve_import_alias(top_level_name, assignment.names)
            full_basename = basename.replace(top_level_name, import_name, 1)
            break
        elif isinstance(assignment, astroid.nodes.ClassDef):
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
    :type: str or None
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

    :returns: True if the function is a contructor, False otherwise.
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
