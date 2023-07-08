"""AutoAPI directives"""

from docutils.parsers.rst import Directive
from docutils import nodes

from sphinx.ext.autosummary import Autosummary, mangle_signature
from sphinx.util.nodes import nested_parse_with_titles

from .mappers.python.objects import PythonFunction


class AutoapiSummary(Autosummary):
    """A version of autosummary that uses static analysis."""

    def get_items(self, names):
        items = []
        env = self.state.document.settings.env
        all_objects = env.autoapi_all_objects
        max_item_chars = 60

        for name in names:
            obj = all_objects[name]
            if isinstance(obj, PythonFunction):
                if obj.overloads:
                    sig = "(\u2026)"
                else:
                    sig = f"({obj.args})"
                    if obj.return_annotation is not None:
                        sig += f" \u2192 {obj.return_annotation}"
            else:
                sig = ""

            if sig:
                max_sig_chars = max(10, max_item_chars - len(obj.short_name))
                sig = mangle_signature(sig, max_chars=max_sig_chars)

            item = (obj.short_name, sig, obj.summary, obj.id)
            items.append(item)

        return items


class NestedParse(Directive):

    """Nested parsing to remove the first heading of included rST

    This is used to handle the case where we like to remove user supplied
    headings from module docstrings. This is required to reduce the number of
    duplicate headings on sections.
    """

    has_content = 1
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        node = nodes.container()
        node.document = self.state.document
        nested_parse_with_titles(self.state, self.content, node)
        try:
            title_node = node[0][0]
            if isinstance(title_node, nodes.title):
                del node[0][0]
        except IndexError:
            pass
        return node.children
