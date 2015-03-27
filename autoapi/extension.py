# -*- coding: utf-8 -*-
"""
Sphinx Auto-API
"""

import os
import yaml
from collections import defaultdict

from docutils import nodes
from docutils import utils

from sphinx.util.osutil import ensuredir

from jinja2 import Environment, FileSystemLoader
from .utils import TEMPLATE_DIR

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


class DotNetMember(object):

    def __init__(self, obj):
        self.obj = obj

    def render(self):
        print "Unknown Type: %s (%s)" % (self.obj['type'], self.obj['name'])
        self.obj['underline'] = len(self.obj['qualifiedName']['CSharp']) * "#"
        self.obj['lower'] = self.obj['type'].lower()
        template = env.get_template('member.rst')
        return template.render(**self.obj)


class DotNetClass(object):

    def __init__(self, obj):
        self.obj = obj
        self.item_map = defaultdict(list)
        self.sort()

    def sort(self):
        for item in self.obj['items']:
            if 'type' not in item:
                print "Missing Type: %s" % item
                continue
            self.item_map[item['type']].append(item)

    def render(self):
        print "Rendering class %s" % self.obj['name']
        self.obj['underline'] = len(self.obj['qualifiedName']['CSharp']) * "#"
        template = env.get_template('class.rst')

        ctx = self.obj
        ctx.update(dict(
            ctors=self.item_map['Constructor'],
            methods=self.item_map['Method'],
            attributes=self.item_map['Property'],
        ))
        return template.render(**ctx)


def parse(obj):
    if 'type' not in obj:
        return ''

    if obj['type'] == 'Class':
        return DotNetClass(obj).render()
    if obj['type'] == 'Namespace':
        return '' #for now
    else:
        return DotNetMember(obj).render()


def load_yaml(app):
    if not app.config.autoapi_dir:
        return
    app.env.autoapi_data = []
    if app.config.autoapi_type == 'yaml':
        for _file in os.listdir(app.env.config.autoapi_dir):
            print "Loading Yaml from %s" % _file
            to_open = os.path.join(app.env.config.autoapi_dir, _file)
            app.env.autoapi_data.append(yaml.safe_load(open(to_open, 'r')))
    app.env.autoapi_enabled = True

    # Generate RST
    for obj in app.env.autoapi_data:
        print "Parsing %s" % obj['name']
        rst = parse(obj)
        if rst:
            path = os.path.join(app.config.autoapi_root, '%s.rst' % obj['name']['CSharp'])
            ensuredir(app.config.autoapi_root)
            with open(path, 'w+') as fp:
                fp.write(rst)


def doctree_read(app, doctree):
    pass

    # para = nodes.paragraph('Test Para', 'Test Para')
    # new_doc = utils.new_document(para)


def env_updated(app, env):
    # env.found_docs.add(os.path.join(app.config.autoapi_root, 'test'))
    pass


def collect_pages(app):
    pass

    context = {
        'title': 'Test Title',
        'body': 'Fak',
    }

    yield (os.path.join(app.config.autoapi_root, 'test_insert'), context, 'page.html')


def setup(app):
    app.connect('doctree-read', doctree_read)
    app.connect('builder-inited', load_yaml)
    app.connect('env-updated', env_updated)
    app.connect('html-collect-pages', collect_pages)
    app.add_config_value('autoapi_type', 'yaml', 'html')
    app.add_config_value('autoapi_root', 'autoapi', 'html')
    app.add_config_value('autoapi_dir', '/Users/eric/projects/sphinx-dotnet-test/examples/yaml/', 'html')
