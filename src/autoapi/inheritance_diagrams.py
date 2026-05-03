import astroid
import sphinx.ext.inheritance_diagram


def _do_import_class(name, currmodule=None):
    path_stack = list(reversed(name.split(".")))
    if not currmodule:
        currmodule = path_stack.pop()

    try:
        target = astroid.MANAGER.ast_from_module_name(currmodule)
        while target and path_stack:
            path_part = path_stack.pop()
            target = (target.getattr(path_part) or (None,))[0]
            while isinstance(target, (astroid.ImportFrom, astroid.Import)):
                try:
                    target = target.do_import_module(path_part)
                except astroid.AstroidImportError:
                    target = target.do_import_module()
                    target = (target.getattr(path_part) or (None,))[0]
                    break
    except astroid.AstroidError:
        target = None

    return target


def _import_class(name, currmodule):
    target = None
    if currmodule:
        target = _do_import_class(name, currmodule)

    if target is None:
        target = _do_import_class(name)

    if not target:
        raise sphinx.ext.inheritance_diagram.InheritanceException(
            f"Could not import class or module {name} specified for inheritance diagram"
        )

    if isinstance(target, astroid.ClassDef):
        return [target]

    if isinstance(target, astroid.Module):
        classes = []
        for child in target.get_children():
            if isinstance(child, astroid.ClassDef):
                classes.append(child)
        return classes

    raise sphinx.ext.inheritance_diagram.InheritanceException(
        f"{name} specified for inheritance diagram is not a class or module"
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
    ):
        all_classes = {}

        def recurse(cls):
            if cls in all_classes:
                return
            if not show_builtins and cls.root().name == "builtins":
                return
            if not private_bases and cls.name.startswith("_"):
                return

            nodename = self.class_name(cls, parts, aliases)
            fullname = self.class_name(cls, 0, aliases)

            tooltip = None
            if cls.doc_node:
                doc = cls.doc_node.value.strip().split("\n")[0]
                if doc:
                    tooltip = '"%s"' % doc.replace('"', '\\"')

            baselist = []
            all_classes[cls] = (nodename, fullname, baselist, tooltip or "")

            if fullname in top_classes:
                return

            for base in cls.ancestors(recurs=False):
                if not show_builtins and base.root().name == "builtins":
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
            return super().run()
        finally:
            sphinx.ext.inheritance_diagram.InheritanceGraph = old_graph
