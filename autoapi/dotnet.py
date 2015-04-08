from collections import defaultdict

from .base import AutoAPIBase
from .settings import env


class DotNetBase(AutoAPIBase):

    language = 'dotnet'

    def __init__(self, obj):
        super(DotNetBase, self).__init__(obj)
        self.name = obj['qualifiedName']['CSharp']
        if hasattr(obj, 'sort'):
            self.sort()

    def render(self, ctx=None):
        if not ctx:
            ctx = {}
        added_ctx = {
            'underline': len(self.name) * self.header
        }
        added_ctx.update(**ctx)
        return super(DotNetBase, self).render(ctx=added_ctx)


class DotNetNamespace(DotNetBase):
    type = 'namespace'
    header = '='

    def render(self, **kwargs):
        ret = super(DotNetNamespace, self).render(**kwargs)
        # import ipdb; ipdb.set_trace()
        return ret

class DotNetClass(object):

    def __init__(self, obj):
        self.obj = obj
        self.item_map = defaultdict(list)
        self.sort()

    def sort(self):
        from .utils import classify
        for item in self.obj.get('items', []):
            if 'type' not in item:
                print "Missing Type: %s" % item
                continue
            self.item_map[item['type']].append(classify(item, 'dotnet'))

    def render(self, indent=4):
        # print "Rendering class %s" % self.obj['name']
        self.obj['underline'] = len(self.obj['qualifiedName']['CSharp']) * "#"
        template = env.get_template('dotnet/class.rst')

        ctx = self.obj
        ctx.update(dict(
            ctors=self.item_map['Constructor'],
            methods=self.item_map['Method'],
            attributes=self.item_map['Property'],
        ))
        return template.render(**ctx)
