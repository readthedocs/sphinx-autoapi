from collections import defaultdict

from .base import AutoAPIBase
from .settings import env


class DotNetBase(AutoAPIBase):

    language = 'dotnet'

    def __init__(self, obj):
        super(DotNetBase, self).__init__(obj)
        # Always exist
        self.id = obj['id']
        self.type = obj['type']
        # Use name or id
        try:
            self.name = obj['qualifiedName']['CSharp']
        except:
            self.name = self.id
        self.short_name = self.name.split('.')[-1]
        self.namespace = self.name.split('.')[0]

        # Optional
        self.summary = obj.get('summary', '')
        if 'syntax' in obj:
            self.syntax = obj['syntax']['content']['CSharp']
        else:
            self.syntax = ''
        self.children = obj.get('items', [])
        if self.children:
            self.item_map = defaultdict(list)
            self.sort()

    def sort(self):
        from .utils import classify
        for item in self.children:
            if 'type' not in item:
                print "Missing Type: %s" % item
                continue
            classified = classify(item, 'dotnet')
            self.item_map[item['type']].append(classified)


class DotNetNamespace(DotNetBase):
    type = 'namespace'


class DotNetMethod(DotNetBase):
    type = 'method'


class DotNetProperty(DotNetBase):
    type = 'property'


class DotNetEnum(DotNetBase):
    type = 'enum'


class DotNetStruct(DotNetBase):
    type = 'struct'


class DotNetConstructor(DotNetBase):
    type = 'constructor'


class DotNetInterface(DotNetBase):
    type = 'interface'


class DotNetDelegate(DotNetBase):
    type = 'delegate'


class DotNetClass(DotNetBase):
    type = 'class'


class DotNetField(DotNetBase):
    type = 'field'

class DotNetEvent(DotNetBase):
    type = 'event'
