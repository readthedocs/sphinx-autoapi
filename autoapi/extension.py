# -*- coding: utf-8 -*-
"""
Sphinx Auto-API Top-level Extension.

This extension allows you to automagically generate API documentation from your project.
"""
import os
import shutil

from docutils import nodes
from sphinx import addnodes
from sphinx.util.console import darkgreen, bold
from sphinx.addnodes import toctree
from sphinx.errors import ExtensionError
from docutils.parsers.rst import directives

from .backends import default_file_mapping, default_ignore_patterns, default_backend_mapping
from .directives import NestedParse
from .settings import API_ROOT

default_options = ['members', 'undoc-members', 'private-members', 'special-members']


def run_autoapi(app):
    """
    Load AutoAPI data from the filesystem.
    """

    if not app.config.autoapi_dirs:
        raise ExtensionError('You must configure an autoapi_dirs setting')

    # Make sure the paths are full
    normalized_dirs = []
    autoapi_dirs = app.config.autoapi_dirs
    if isinstance(autoapi_dirs, str):
        autoapi_dirs = [autoapi_dirs]
    for path in autoapi_dirs:
        if os.path.isabs(path):
            normalized_dirs.append(path)
        else:
            normalized_dirs.append(
                os.path.normpath(os.path.join(app.confdir, path))
            )

    for _dir in normalized_dirs:
        if not os.path.exists(_dir):
            raise ExtensionError(
                'AutoAPI Directory `{dir}` not found. '
                'Please check your `autoapi_dirs` setting.'.format(
                    dir=_dir
                )
            )

    normalized_root = os.path.normpath(os.path.join(app.confdir, app.config.autoapi_root))
    url_root = os.path.join('/', app.config.autoapi_root)

    app.env.autoapi_data = []

    domain = default_backend_mapping[app.config.autoapi_type]
    domain_obj = domain(app, template_dir=app.config.autoapi_template_dir,
                        url_root=url_root)

    if app.config.autoapi_file_patterns:
        file_patterns = app.config.autoapi_file_patterns
    else:
        file_patterns = default_file_mapping.get(app.config.autoapi_type, [])

    if app.config.autoapi_ignore:
        ignore_patterns = app.config.autoapi_ignore
    else:
        ignore_patterns = default_ignore_patterns.get(app.config.autoapi_type, [])

    if '.rst' in app.config.source_suffix:
        out_suffix = '.rst'
    elif '.txt' in app.config.source_suffix:
        out_suffix = '.txt'
    else:
        # Fallback to first suffix listed
        out_suffix = app.config.source_suffix[0]

    # Actual meat of the run.
    app.info(bold('[AutoAPI] ') + darkgreen('Loading Data'))
    domain_obj.load(
        patterns=file_patterns,
        dirs=normalized_dirs,
        ignore=ignore_patterns,
    )

    app.info(bold('[AutoAPI] ') + darkgreen('Mapping Data'))
    domain_obj.map(options=app.config.autoapi_options)

    app.info(bold('[AutoAPI] ') + darkgreen('Rendering Data'))
    domain_obj.output_rst(
        root=normalized_root,
        source_suffix=out_suffix,
    )


def build_finished(app, exception):
    if not app.config.autoapi_keep_files:
        normalized_root = os.path.normpath(os.path.join(app.confdir, app.config.autoapi_root))
        if app.verbosity > 1:
            app.info(bold('[AutoAPI] ') + darkgreen('Cleaning generated .rst files'))
        shutil.rmtree(normalized_root)

        mapper = default_backend_mapping[app.config.autoapi_type]
        if hasattr(mapper, 'build_finished'):
            mapper.build_finished(app, exception)


def doctree_read(app, doctree):
    all_docs = set()
    insert = True
    if app.env.docname == 'index':
        nodes = doctree.traverse(toctree)
        if not nodes:
            return
        for node in nodes:
            for entry in node['entries']:
                all_docs.add(entry[1])
        for doc in all_docs:
            if doc.find(app.config.autoapi_root) != -1:
                insert = False
        if insert and app.config.autoapi_add_toctree_entry:
            nodes[-1]['entries'].append(
                (None, u'%s/index' % app.config.autoapi_root)
            )
            nodes[-1]['includefiles'].append(u'%s/index' % app.config.autoapi_root)
            app.info(bold('[AutoAPI] ') + darkgreen('Adding AutoAPI TOCTree to index.rst'))


def _build_toc_node(docname, anchor='anchor', text='test text', bullet=False):
    reference = nodes.reference('', '', internal=True, refuri=docname,
                                anchorname='#' + anchor, *[nodes.Text(text, text)])
    para = addnodes.compact_paragraph('', '', reference)
    ret_list = nodes.list_item('', para)
    if not bullet:
        return ret_list
    else:
        return nodes.bullet_list('', ret_list)


def _find_toc_node(toc, ref_id, objtype):
    for check_node in toc.traverse(nodes.reference):
        if objtype == nodes.section and \
                (check_node.attributes['refuri'] == ref_id or
                 check_node.attributes['anchorname'] == '#' + ref_id):
            return check_node
        if objtype == addnodes.desc and check_node.attributes['anchorname'] == '#' + ref_id:
            return check_node
    return None


def _traverse_parent(node, objtypes):
    curr_node = node.parent
    while curr_node is not None:
        if isinstance(curr_node, objtypes):
            return curr_node
        curr_node = curr_node.parent
    return None


def doctree_resolved(app, doctree, docname):
    "Add domain objects to the toctree"

    toc = app.env.tocs[docname]
    for desc_node in doctree.traverse(addnodes.desc):
        # objtype = desc_node.attributes.get('objtype')
        # if objtype == 'class':
        ref_id = desc_node.children[0].attributes['ids'][0]
        try:
            ref_text = desc_node[0].attributes['fullname'].split('.')[-1].split('(')[0]
        except:
            ref_text = desc_node[0].astext().split('.')[-1].split('(')[0]
        parent_node = _traverse_parent(node=desc_node, objtypes=(addnodes.desc, nodes.section))
        if parent_node:
            if isinstance(parent_node, nodes.section) and \
                    isinstance(parent_node.parent, nodes.document):
                # Top Level Section header
                parent_ref_id = docname
                toc_reference = _find_toc_node(toc, parent_ref_id, nodes.section)
            elif isinstance(parent_node, nodes.section):
                # Nested Section header
                parent_ref_id = parent_node.attributes['ids'][0]
                toc_reference = _find_toc_node(toc, parent_ref_id, nodes.section)
            else:
                # Desc node
                parent_ref_id = parent_node.children[0].attributes['ids'][0]
                toc_reference = _find_toc_node(toc, parent_ref_id, addnodes.desc)

            if toc_reference:
                # The last bit of the parent we're looking at
                toc_insertion_point = _traverse_parent(toc_reference, nodes.bullet_list)[-1]
                if toc_insertion_point and isinstance(toc_insertion_point[0], nodes.bullet_list):
                    new_insert = toc_insertion_point[0]
                    to_add = _build_toc_node(docname, anchor=ref_id, text=ref_text)
                    new_insert.append(to_add)
                else:
                    to_add = _build_toc_node(docname, anchor=ref_id, text=ref_text, bullet=True)
                    toc_insertion_point.append(to_add)


def setup(app):
    app.connect('builder-inited', run_autoapi)
    app.connect('build-finished', build_finished)
    app.connect('doctree-read', doctree_read)
    app.connect('doctree-resolved', doctree_resolved)
    app.add_config_value('autoapi_type', 'python', 'html')
    app.add_config_value('autoapi_root', API_ROOT, 'html')
    app.add_config_value('autoapi_ignore', [], 'html')
    app.add_config_value('autoapi_options', default_options, 'html')
    app.add_config_value('autoapi_file_patterns', None, 'html')
    app.add_config_value('autoapi_dirs', [], 'html')
    app.add_config_value('autoapi_keep_files', False, 'html')
    app.add_config_value('autoapi_add_toctree_entry', True, 'html')
    app.add_config_value('autoapi_template_dir', [], 'html')
    app.add_stylesheet('autoapi.css')
    directives.register_directive('autoapi-nested-parse', NestedParse)
