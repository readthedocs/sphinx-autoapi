# -*- coding: utf-8 -*-
"""
Sphinx Auto-API
"""

import os
import yaml
import fnmatch
import shutil
from collections import defaultdict

from sphinx.util.osutil import ensuredir
from sphinx.util.console import bold, darkgreen

from .utils import classify
# from .dotnet import DotNetNamespace

from epyparse import parsed


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
    namespaces = defaultdict(list)

    if app.config.autoapi_type == 'dotnet':

        print "Reading Autodoc Yaml"
        # Load Yaml
        files_to_read = os.listdir(app.config.autoapi_dir)
        for _file in app.status_iterator(
                files_to_read, '[AutoAPI] Reading files... ', darkgreen, len(files_to_read)):
            # print "Loading Yaml from %s" % _file
            to_open = os.path.join(app.config.autoapi_dir, _file)
            yaml_obj = yaml.safe_load(open(to_open, 'r'))
            app.env.autoapi_data.append(classify(yaml_obj, 'dotnet'))

        # print "Sorting objects"
        # Sort objects
        # for obj in app.env.autoapi_data:
            # obj_name = obj['qualifiedName']['CSharp']
            # namespace = obj_name.split('.')[0]
            # namespaces[namespace].append(classify(obj, 'dotnet'))
            # rst = parse(obj, 'dotnet')
            # if rst:
            #     path = os.path.join(app.config.autoapi_root, '%s%s' % (obj['name']['CSharp'], app.config.source_suffix[0]))
            #     ensuredir(app.config.autoapi_root)
            #     with open(path, 'w+') as fp:
            #         fp.write(rst)

        print "Generating RST"
        # Generate RST
        # for namespace, objs in namespaces.items():
        for obj in app.env.autoapi_data:
            # path = os.path.join(app.config.autoapi_root, '%s%s' % (namespace, app.config.source_suffix[0]))
            # namespace_obj = DotNetNamespace(namespace, objs)
            # ensuredir(app.config.autoapi_root)
            # with open(path, 'w+') as index_file:
            #     namespace_rst = namespace_obj.render()
            #     if namespace_rst:
            #         index_file.write(namespace_rst)
            # for obj in objs:
                rst = obj.render()
                # Detail
                detail_dir = os.path.join(app.config.autoapi_root, obj.obj['type'])
                ensuredir(detail_dir)
                path = os.path.join(detail_dir, '%s%s' % (obj.obj['name']['CSharp'], app.config.source_suffix[0]))
                if rst:
                    with open(path, 'w+') as detail_file:
                        detail_file.write(rst)

    elif app.config.autoapi_type == 'python':
        for root, dirnames, filenames in os.walk(app.config.autoapi_dir):
            for filename in fnmatch.filter(filenames, u'*.py'):
                to_open = os.path.join(root, filename)
                if ignore_file(app, to_open):
                    continue
                # print "Parsing Python File from %s" % to_open
                try:
                    parsed_data = parsed(to_open)
                    app.env.autoapi_data.append(parsed_data)
                except Exception:
                    print "Exception, Keeping going: %s" % to_open
                    import traceback
                    traceback.print_exc()
        app.env.autoapi_enabled = True

        # Generate RST
        for obj in app.env.autoapi_data:
            # print "Parsing %s" % obj['fullname']
            rst = classify(obj, 'python').render()
            if rst:
                path = os.path.join(app.config.autoapi_root, '%s%s' % (obj['fullname'], app.config.source_suffix[0]))
                ensuredir(app.config.autoapi_root)
                with open(path, 'w+') as fp:
                    fp.write(rst.encode('utf8'))


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
