"""AutoAPI directives"""

import posixpath
import re

from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from docutils import nodes

from sphinx import addnodes
import sphinx.ext.autosummary
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.util.rst import escape


class AutoapiSummary(Directive):
    """A version of autosummary that uses static analysis."""

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True
    option_spec = {
        "toctree": directives.unchanged,
        "nosignatures": directives.flag,
        "template": directives.unchanged,
    }

    def warn(self, msg):
        """Add a warning message.

        :param msg: The warning message to add.
        :type msg: str
        """
        self.warnings.append(
            self.state.document.reporter.warning(msg, line=self.lineno)
        )

    def _get_names(self):
        """Get the names of the objects to include in the table.

        :returns: The names of the objects to include.
        :rtype: generator(str)
        """
        for line in self.content:
            line = line.strip()
            if line and re.search("^[a-zA-Z0-9]", line):
                yield line

    def run(self):
        self.warnings = []

        env = self.state.document.settings.env
        mapper = env.autoapi_mapper

        objects = [mapper.all_objects[name] for name in self._get_names()]
        nodes_ = self._get_table(objects)

        if "toctree" in self.options:
            dirname = posixpath.dirname(env.docname)

            tree_prefix = self.options["toctree"].strip()
            docnames = []
            for obj in objects:
                docname = posixpath.join(tree_prefix, obj.name)
                docname = posixpath.normpath(posixpath.join(dirname, docname))
                if docname not in env.found_docs:
                    self.warn("toctree references unknown document {}".format(docname))
                docnames.append(docname)

            tocnode = addnodes.toctree()
            tocnode["includefiles"] = docnames
            tocnode["entries"] = [(None, docn) for docn in docnames]
            tocnode["maxdepth"] = -1
            tocnode["glob"] = None

            tocnode = sphinx.ext.autosummary.autosummary_toc("", "", tocnode)
            nodes_.append(tocnode)

        return self.warnings + nodes_

    def _get_row(self, obj):
        template = ":{}:`{} <{}>`\\ {}"
        if "nosignatures" in self.options:
            template = ":{}:`{} <{}>`"

        col1 = template.format(
            "obj", obj.short_name, obj.name, escape("({})".format(obj.args))
        )
        col2 = obj.summary

        row = nodes.row("")
        for text in (col1, col2):
            node = nodes.paragraph("")
            view_list = ViewList()
            view_list.append(text, "<autosummary>")
            self.state.nested_parse(view_list, 0, node)
            try:
                if isinstance(node[0], nodes.paragraph):
                    node = node[0]
            except IndexError:
                pass
            row.append(nodes.entry("", node))

        return row

    def _get_table(self, objects):
        table_spec = addnodes.tabular_col_spec()
        table_spec["spec"] = r"p{0.5\linewidth}p{0.5\linewidth}"

        table = sphinx.ext.autosummary.autosummary_table("")
        real_table = nodes.table("", classes=["longtable"])
        table.append(real_table)
        group = nodes.tgroup("", cols=2)
        real_table.append(group)
        group.append(nodes.colspec("", colwidth=10))
        group.append(nodes.colspec("", colwidth=90))
        body = nodes.tbody("")
        group.append(body)

        for obj in objects:
            body.append(self._get_row(obj))

        return [table_spec, table]


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
