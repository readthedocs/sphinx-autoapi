# -*- coding: utf-8 -*-
"""
Sphinx Auto-API
"""

import fnmatch
import shutil

from .domains import DotNetDomain, PythonDomain


def ignore_file(app, filename):
    for pat in app.config.autoapi_ignore:
        if fnmatch.fnmatch(filename, pat):
            return True
    return False


def load_yaml(app):
    if not app.config.autoapi_dir:
        print "You must configure an autodapi_dir setting."
        return
    app.env.autoapi_data = []

    if app.config.autoapi_type == 'dotnet':
        domain = DotNetDomain(app)
    elif app.config.autoapi_type == 'python':
       domain = PythonDomain(app)
    domain.full()


def build_finished(app, exception):
    if not app.config.autoapi_keep_files:
        if app.verbosity > 1:
            print "Cleaning autoapi out"
        shutil.rmtree(app.config.autoapi_root)


def setup(app):
    app.connect('builder-inited', load_yaml)
    app.connect('build-finished', build_finished)
    app.add_config_value('autoapi_type', 'dotnet', 'html')
    app.add_config_value('autoapi_root', 'autoapi', 'html')
    app.add_config_value('autoapi_ignore', ['*migrations*'], 'html')
    app.add_config_value('autoapi_dir', '', 'html')
    app.add_config_value('autoapi_keep_files', True, 'html')
    app.add_stylesheet('autoapi.css')
