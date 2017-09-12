try:
    import builtins
except ImportError:
    import __builtin__ as builtins
import re

import astroid
import astroid.nodes


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
    """Get the full path of a name from an ``import x from y`` statement.

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
            import_from.modname, level=import_from.level,
        )

    return '{}.{}'.format(module_name, partial_basename)


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

    top_level_name = re.sub(r'\(.*\)', '', basename).split('.', 1)[0]
    lookup_node = node
    while not hasattr(lookup_node, 'lookup'):
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

    if isinstance(node, astroid.nodes.Call):
        full_basename = re.sub(r'\(.*\)', '()', full_basename)

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
    :type node: astroid.nodes.Assign

    :returns: The name that is assigned to,
        and the value assigned to the name (if it can be converted).
    :rtype: tuple(str, object or None) or None
    """
    if len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, astroid.nodes.AssignName):
            name = target.name
        elif isinstance(target, astroid.nodes.AssignAttr):
            name = target.attrname
        else:
            return None
        return (name, _get_const_values(node.value))

    return None


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
            class_node.name == 'property'
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
        if (isinstance(decorator, astroid.nodes.Attribute)
                and decorator.attrname == "setter"):
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
        and node.name == '__init__'
    )
