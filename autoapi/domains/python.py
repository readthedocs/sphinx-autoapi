import sys
from collections import defaultdict

from epyparse import parsed

from ..base import AutoAPIBase
from ..settings import env

#        for root, dirnames, filenames in os.walk(app.config.autoapi_dir):
#            for filename in fnmatch.filter(filenames, u'*.py'):
#                to_open = os.path.join(root, filename)
#                if ignore_file(app, to_open):
#                    continue
#                # print "Parsing Python File from %s" % to_open
#                try:
#                    parsed_data = parsed(to_open)
#                    app.env.autoapi_data.append(parsed_data)
#                except Exception:
#                    print "Exception, Keeping going: %s" % to_open
#                    import traceback
#                    traceback.print_exc()
#        app.env.autoapi_enabled = True
#
#        # Generate RST
#        for obj in app.env.autoapi_data:
#            # print "Parsing %s" % obj['fullname']
#            rst = classify(obj, 'python').render()
#            if rst:
#                path = os.path.join(app.config.autoapi_root, '%s%s' % (obj['fullname'], app.config.source_suffix[0]))
#                ensuredir(app.config.autoapi_root)
#                with open(path, 'w+') as fp:
#                    fp.write(rst.encode('utf8'))

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
