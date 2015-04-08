import sys
from collections import defaultdict

from .base import AutoAPIBase
from .settings import env


class PythonBase(AutoAPIBase):

    language = 'python'

    def __init__(self, obj):
        obj = super(PythonBase, self).__init__(obj)
        obj.name = obj['fullname']

    def render(self, ctx):
        added_ctx = {
            'underline': len(self.name) * self.header
        }
        added_ctx.update(**ctx)
        super(PythonBase, self).render(ctx=added_ctx)


class PythonFunction(PythonBase):
    type = 'function'


class PythonModule(object):

    def __init__(self, obj):
        self.obj = obj
        self.item_map = defaultdict(list)
        self.sort()

    def sort(self):
        from .utils import classify
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
        from .utils import classify
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
