import sys

import astroid
import sphinx.ext.inheritance_diagram

if sys.version_info >= (3,):
    _BUILTINS = "builtins"
else:
    _BUILTINS = "__builtins__"


def _import_class(name, currmodule):
    path_stack = list(reversed(name.split(".")))
    target = None
    if currmodule:
        try:
            target = astroid.MANAGER.ast_from_module_name(currmodule)
            while target and path_stack:
                target = (target.getattr(path_stack.pop()) or (None,))[0]
        except astroid.AstroidError:
            target = None

    if target is None:
        path_stack = list(reversed(name.split(".")))
        try:
            target = astroid.MANAGER.ast_from_module_name(path_stack.pop())
            while target and path_stack:
                target = (target.getattr(path_stack.pop()) or (None,))[0]
        except astroid.AstroidError:
            target = None

    if not target:
        raise sphinx.ext.inheritance_diagram.InheritanceException(
            "Could not import class or module {} specified for inheritance diagram".format(
                name
            )
        )

    if isinstance(target, astroid.ClassDef):
        return [target]

    if isinstance(target, astroid.Module):
        classes = []
        for child in target.children:
            if isinstance(child, astroid.ClassDef):
                classes.append(child)
        return classes

    raise sphinx.ext.inheritance_diagram.InheritanceException(
        "{} specified for inheritance diagram is not a class or module".format(name)
    )


class _AutoapiInheritanceGraph(sphinx.ext.inheritance_diagram.InheritanceGraph):
    @staticmethod
    def _import_classes(class_names, currmodule):
        classes = []

        for name in class_names:
            classes.extend(_import_class(name, currmodule))

        return classes

    def _class_info(
        self, classes, show_builtins, private_bases, parts, aliases, top_classes
    ):  # pylint: disable=too-many-arguments
        all_classes = {}

        def recurse(cls):
            if cls in all_classes:
                return
            if not show_builtins and cls.root().name == _BUILTINS:
                return
            if not private_bases and cls.name.startswith("_"):
                return

            nodename = self.class_name(cls, parts, aliases)
            fullname = self.class_name(cls, 0, aliases)

            tooltip = None
            if cls.doc:
                doc = cls.doc.strip().split("\n")[0]
                if doc:
                    tooltip = '"%s"' % doc.replace('"', '\\"')

            baselist = []
            all_classes[cls] = (nodename, fullname, baselist, tooltip)

            if fullname in top_classes:
                return

            for base in cls.ancestors(recurs=False):
                if not show_builtins and base.root().name == _BUILTINS:
                    continue
                if not private_bases and base.name.startswith("_"):
                    continue
                baselist.append(self.class_name(base, parts, aliases))
                if base not in all_classes:
                    recurse(base)

        for cls in classes:
            recurse(cls)

        return list(all_classes.values())

    @staticmethod
    def class_name(node, parts=0, aliases=None):
        fullname = node.qname()
        if fullname.startswith(("__builtin__.", "builtins")):
            fullname = fullname.split(".", 1)[-1]
        if parts == 0:
            result = fullname
        else:
            name_parts = fullname.split(".")
            result = ".".join(name_parts[-parts:])
        if aliases is not None and result in aliases:
            return aliases[result]
        return result


class AutoapiInheritanceDiagram(sphinx.ext.inheritance_diagram.InheritanceDiagram):
    def run(self):
        # Yucky! Monkeypatch InheritanceGraph to use our own
        old_graph = sphinx.ext.inheritance_diagram.InheritanceGraph
        sphinx.ext.inheritance_diagram.InheritanceGraph = _AutoapiInheritanceGraph
        try:
            return super(AutoapiInheritanceDiagram, self).run()
        finally:
            sphinx.ext.inheritance_diagram.InheritanceGraph = old_graph
