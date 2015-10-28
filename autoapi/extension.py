# -*- coding: utf-8 -*-
"""
Sphinx Auto-API Top-level Extension.

This extension allows you to automagically generate API documentation from your project.
"""
import os
import shutil

from sphinx.util.console import darkgreen, bold
from sphinx.addnodes import toctree
from sphinx.errors import ExtensionError

from .backends import default_file_mapping, default_ignore_patterns, default_backend_mapping
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
    for path in app.config.autoapi_dirs:
        if os.path.isabs(path):
            normalized_dirs.append(app.config.autoapi_dir)
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
        # TODO: Better way to determine suffix?
        source_suffix=app.config.source_suffix[0],
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


def setup(app):
    app.connect('builder-inited', run_autoapi)
    app.connect('build-finished', build_finished)
    app.connect('doctree-read', doctree_read)
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
