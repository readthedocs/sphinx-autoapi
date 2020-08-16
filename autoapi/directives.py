"""AutoAPI directives"""

from docutils.parsers.rst import Directive
from docutils import nodes

from sphinx.ext.autosummary import Autosummary
from sphinx.util.nodes import nested_parse_with_titles

from .mappers.python.objects import PythonFunction


class AutoapiSummary(Autosummary):  # pylint: disable=too-few-public-methods
    """A version of autosummary that uses static analysis."""

    def get_items(self, names):
        items = []
        env = self.state.document.settings.env
        mapper = env.autoapi_mapper

        for name in names:
            obj = mapper.all_objects[name]
            if isinstance(obj, PythonFunction):
                if obj.overloads:
                    sig = "(\u2026)"
                else:
                    sig = "({})".format(obj.args)
                    if obj.return_annotation is not None:
                        sig += " \u2192 {}".format(obj.return_annotation)
            else:
                sig = ""

            item = (obj.short_name, sig, obj.summary, obj.id)
            items.append(item)

        return items


class NestedParse(Directive):  # pylint: disable=too-few-public-methods

    """Nested parsing to remove the first heading of included rST

    This is used to handle the case where we like to remove user supplied
    headings from module docstrings. This is required to reduce the number of
    duplicate headings on sections.
    """

    has_content = 1
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

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
