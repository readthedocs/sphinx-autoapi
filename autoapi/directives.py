"""AutoAPI directives"""

from docutils.parsers.rst import Directive
from docutils import nodes

from sphinx.util.nodes import nested_parse_with_titles


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
    option_spec = {}

    def run(self):
        node = nodes.paragraph()
        node.document = self.state.document
        nested_parse_with_titles(self.state, self.content, node)
        try:
            title_node = node[0][0]
            if isinstance(title_node, nodes.title):
                del node[0][0]
        except IndexError:
            pass
        return [node]
