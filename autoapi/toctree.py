"""
A small Sphinx extension that adds Domain objects (eg. Python Classes & Methods) to the TOC Tree.

It dynamically adds them to the already rendered ``app.env.tocs`` dict on the Sphinx environment.
Traditionally this only contains Section's,
we then nest our Domain references inside the already existing Sections.
"""

from docutils import nodes
from sphinx import addnodes
import sphinx.util.logging

LOGGER = sphinx.util.logging.getLogger(__name__)


def _build_toc_node(docname, anchor="anchor", text="test text", bullet=False):
    """
    Create the node structure that Sphinx expects for TOC Tree entries.

    The ``bullet`` argument wraps it in a ``nodes.bullet_list``,
    which is how you nest TOC Tree entries.
    """
    reference = nodes.reference(
        "",
        "",
        internal=True,
        refuri=docname,
        anchorname="#" + anchor,
        *[nodes.Text(text, text)]
    )
    para = addnodes.compact_paragraph("", "", reference)
    ret_list = nodes.list_item("", para)
    return nodes.bullet_list("", ret_list) if bullet else ret_list


def _traverse_parent(node, objtypes):
    """
    Traverse up the node's parents until you hit the ``objtypes`` referenced.

    Can either be a single type,
    or a tuple of types.
    """
    curr_node = node.parent
    while curr_node is not None:
        if isinstance(curr_node, objtypes):
            return curr_node
        curr_node = curr_node.parent
    return None


def _find_toc_node(toc, ref_id, objtype):
    """
    Find the actual TOC node for a ref_id.

    Depends on the object type:
    * Section - First section (refuri) or 2nd+ level section (anchorname)
    * Desc - Just use the anchor name
    """
    for check_node in toc.traverse(nodes.reference):
        if objtype == nodes.section and (
            check_node.attributes["refuri"] == ref_id
            or check_node.attributes["anchorname"] == "#" + ref_id
        ):
            return check_node
        if (
            objtype == addnodes.desc
            and check_node.attributes["anchorname"] == "#" + ref_id
        ):
            return check_node
    return None


def _get_toc_reference(app, node, toc, docname):
    """
    Logic that understands maps a specific node to it's part of the toctree.

    It takes a specific incoming ``node``,
    and returns the actual TOC Tree node that is said reference.
    """
    if isinstance(node, nodes.section) and isinstance(node.parent, nodes.document):
        # Top Level Section header
        ref_id = docname
        toc_reference = _find_toc_node(toc, ref_id, nodes.section)
    elif isinstance(node, nodes.section):
        # Nested Section header
        ref_id = node.attributes["ids"][0]
        toc_reference = _find_toc_node(toc, ref_id, nodes.section)
    else:
        # Desc node
        try:
            ref_id = node.children[0].attributes["ids"][0]
            toc_reference = _find_toc_node(toc, ref_id, addnodes.desc)
        except (KeyError, IndexError) as e:
            LOGGER.warning("Invalid desc node: %s" % e)
            toc_reference = None

    return toc_reference


def add_domain_to_toctree(app, doctree, docname):
    """
    Add domain objects to the toctree dynamically.

    This should be attached to the ``doctree-resolved`` event.
    This works by:

    * Finding each domain node (addnodes.desc)
    * Figuring out it's parent that will be in the toctree
         (nodes.section, or a previously added addnodes.desc)
    * Finding that parent in the TOC Tree based on it's ID
    * Taking that element in the TOC Tree,
      and finding it's parent that is a TOC Listing (nodes.bullet_list)
    * Adding the new TOC element for our specific node as a child of that nodes.bullet_list
        * This checks that bullet_list's last child,
        and checks that it is also a nodes.bullet_list,
        effectively nesting it under that element
    """
    toc = app.env.tocs[docname]
    for desc_node in doctree.traverse(addnodes.desc):
        try:
            ref_id = desc_node.children[0].attributes["ids"][0]
        except (KeyError, IndexError) as e:
            LOGGER.warning("Invalid desc node: %s" % e)
            continue
        try:
            # Python domain object
            ref_text = desc_node[0].attributes["fullname"].split(".")[-1].split("(")[0]
        except (KeyError, IndexError):
            # TODO[eric]: Support other Domains and ways of accessing this data
            # Use `astext` for other types of domain objects
            ref_text = desc_node[0].astext().split(".")[-1].split("(")[0]
        # This is the actual object that will exist in the TOC Tree
        # Sections by default, and other Desc nodes that we've previously placed.
        parent_node = _traverse_parent(
            node=desc_node, objtypes=(addnodes.desc, nodes.section)
        )

        if parent_node:
            toc_reference = _get_toc_reference(app, parent_node, toc, docname)
            if toc_reference:
                # Get the last child of our parent's bullet list, this is where "we" live.
                toc_insertion_point = _traverse_parent(
                    toc_reference, nodes.bullet_list
                )[-1]
                # Ensure we're added another bullet list so that we nest inside the parent,
                # not next to it
                if toc_insertion_point and isinstance(
                    toc_insertion_point[0], nodes.bullet_list
                ):
                    new_insert = toc_insertion_point[0]
                    to_add = _build_toc_node(docname, anchor=ref_id, text=ref_text)
                    new_insert.append(to_add)
                else:
                    to_add = _build_toc_node(
                        docname, anchor=ref_id, text=ref_text, bullet=True
                    )
                    toc_insertion_point.append(to_add)
