# -*- coding: utf-8 -*-
"""
Sphinx Auto-API
"""

import os
import sys
import yaml
import fnmatch
from collections import defaultdict
import traceback

from sphinx.util.osutil import ensuredir

from jinja2 import Environment, FileSystemLoader
from .utils import TEMPLATE_DIR
from epyparse import parsed

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


class DotNetMember(object):

    def __init__(self, obj):
        self.obj = obj

    def render(self):
        print "Unknown Type: %s (%s)" % (self.obj['type'], self.obj['name'])
        self.obj['underline'] = len(self.obj['qualifiedName']['CSharp']) * "~"
        template = env.get_template('member.rst')
        return template.render(**self.obj)


class PythonMember(object):

    def __init__(self, obj):
        self.obj = obj

    def render(self):
        print "Unknown Type: %s (%s)" % (self.obj['type'], self.obj['fullname'])
        self.obj['underline'] = len(self.obj['fullname']) * "~"
        template = env.get_template('python/member.rst')
        try:
            return template.render(**self.obj)
        except Exception, e:
            print "Exception, Keeping going"
            print sys.exc_info()
            return ''


class PythonFunction(object):

    def __init__(self, obj):
        self.obj = obj

    def render(self):
        # print "Rendering function %s" % self.obj['fullname']
        self.obj['underline'] = len(self.obj['fullname']) * "~"
        template = env.get_template('python/function.rst')
        try:
            return template.render(**self.obj)
        except Exception, e:
            print "Exception, Keeping going"
            print sys.exc_info()
            return ''


class PythonModule(object):

    def __init__(self, obj):
        self.obj = obj
        self.item_map = defaultdict(list)
        self.sort()

    def sort(self):
        for item in self.obj.get('children', []):
            if 'type' not in item:
                print "Missing Type: %s" % item
                continue
            self.item_map[item['type']].append(classify(item, 'python'))

    def render(self):
        # print "Rendering module %s" % self.obj['fullname']
        self.obj['underline'] = len(self.obj['fullname']) * "#"
        template = env.get_template('python/module.rst')

        ctx = self.obj
        ctx.update(dict(
            methods=self.item_map['function'],
            classes=self.item_map['class'],
            imports=self.obj['imports'],
        ))
        return template.render(**ctx)


class PythonClass(object):

    def __init__(self, obj):
        self.obj = obj
        self.item_map = defaultdict(list)
        self.sort()

    def sort(self):
        for item in self.obj.get('children', []):
            if 'type' not in item:
                print "Missing Type: %s" % item
                continue
            self.item_map[item['type']].append(classify(item, 'python'))

    def render(self, indent=4):
        # print "Rendering class %s" % self.obj['fullname']
        template = env.get_template('python/class.rst')
        ctx = self.obj
        ctx.update(dict(
            underline=len(self.obj['fullname']) * "-",
            methods=self.item_map['function'],
            classes=self.item_map['class'],
            indent=indent,
        ))
        return template.render(**ctx)


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

    def render(self, indent=4):
        # print "Rendering class %s" % self.obj['name']
        self.obj['underline'] = len(self.obj['qualifiedName']['CSharp']) * "#"
        template = env.get_template('class.rst')

        ctx = self.obj
        ctx.update(dict(
            ctors=self.item_map['Constructor'],
            methods=self.item_map['Method'],
            attributes=self.item_map['Property'],
        ))
        return template.render(**ctx)


def classify(obj, obj_type):
    if 'type' not in obj:
        return ''

    if obj_type == 'python':
        if obj['type'] == 'module':
            if not obj.get('children'):
                return ''
            return PythonModule(obj)
        if obj['type'] == 'class':
            return PythonClass(obj)
        if obj['type'] == 'function':
            return PythonFunction(obj)
        else:
            return PythonMember(obj)
    if obj_type == 'dotnet':
        if obj['type'] == 'Class':
            return DotNetClass(obj)
        if obj['type'] == 'Namespace':
            return ''  # for now
        else:
            return DotNetMember(obj)


def parse(obj, obj_type):
    cls = classify(obj, obj_type)
    if cls:
        return cls.render()


def ignore_file(app, filename):
    for pat in app.config.autoapi_ignore:
        if fnmatch.fnmatch(filename, pat):
            return True
    return False


def load_yaml(app):
    if not app.config.autoapi_dir:
        return
    app.env.autoapi_data = []

    if app.config.autoapi_type == 'dotnet':
        for _file in os.listdir(app.config.autoapi_dir):
            # print "Loading Yaml from %s" % _file
            to_open = os.path.join(app.env.config.autoapi_dir, _file)
            app.env.autoapi_data.append(yaml.safe_load(open(to_open, 'r')))
        # Generate RST
        for obj in app.env.autoapi_data:
            # print "Parsing %s" % obj['name']
            rst = parse(obj, 'dotnet')
            if rst:
                path = os.path.join(app.config.autoapi_root, '%s%s' % (obj['name']['CSharp'], app.config.source_suffix[0]))
                ensuredir(app.config.autoapi_root)
                with open(path, 'w+') as fp:
                    fp.write(rst)

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
                except Exception, e:
                    print "Exception, Keeping going: %s" % to_open
                    print sys.exc_info()
                    import traceback; traceback.print_exc();
        app.env.autoapi_enabled = True

        # Generate RST
        for obj in app.env.autoapi_data:
            # print "Parsing %s" % obj['fullname']
            rst = parse(obj, 'python')
            if rst:
                path = os.path.join(app.config.autoapi_root, '%s%s' % (obj['fullname'], app.config.source_suffix[0]))
                ensuredir(app.config.autoapi_root)
                with open(path, 'w+') as fp:
                    fp.write(rst.encode('utf8'))


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
    app.add_config_value('autoapi_type', 'dotnet', 'html')
    app.add_config_value('autoapi_root', 'autoapi', 'html')
    app.add_config_value('autoapi_ignore', ['*migrations*'], 'html')
    app.add_config_value('autoapi_dir', '', 'html')
