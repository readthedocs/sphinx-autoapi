# -*- coding: utf-8 -*-
"""
Sphinx Auto-API
"""

import os
import fnmatch
import shutil

from .domains import DotNetDomain, PythonDomain, GoDomain, JavaScriptDomain


def ignore_file(app, filename):
    for pat in app.config.autoapi_ignore:
        if fnmatch.fnmatch(filename, pat):
            return True
    return False


def load_yaml(app):
    """
    Load AutoAPI data from the filesystem.
    """

    if not app.config.autoapi_dir:
        print "You must configure an autodapi_dir setting."
        return
    app.env.autoapi_data = []

    mapping = {
        'python': PythonDomain,
        'dotnet': DotNetDomain,
        'go': GoDomain,
        'javascript': JavaScriptDomain,
    }

    domain = mapping[app.config.autoapi_type]
    domain_obj = domain(app)
    app.info('[AutoAPI] Loading Data')
    domain_obj.load(
        pattern=app.config.autoapi_file_pattern,
        dir=os.path.normpath(app.config.autoapi_dir),
        ignore=app.config.autoapi_ignore,
    )
    app.info('[AutoAPI] Mapping Data')
    domain_obj.map()
    app.info('[AutoAPI] Rendering Data')
    domain_obj.output_rst(
        root=app.config.autoapi_root,
        # TODO: Better way to determine suffix?
        source_suffix=app.config.source_suffix[0]
    )


def build_finished(app, exception):
    if not app.config.autoapi_keep_files:
        if app.verbosity > 1:
            print "Cleaning autoapi out"
        shutil.rmtree(app.config.autoapi_root)


def setup(app):
    app.connect('builder-inited', load_yaml)
    app.connect('build-finished', build_finished)
    app.add_config_value('autoapi_type', 'python', 'html')
    app.add_config_value('autoapi_root', 'autoapi', 'html')
    app.add_config_value('autoapi_ignore', ['*migrations*'], 'html')
    app.add_config_value('autoapi_file_pattern', '*', 'html')
    app.add_config_value('autoapi_dir', '', 'html')
    app.add_config_value('autoapi_keep_files', True, 'html')
    app.add_stylesheet('autoapi.css')
