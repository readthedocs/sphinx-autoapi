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

        # Syntax example and parameter list
        syntax = obj.get('syntax', None)
        self.example = ''
        if syntax is not None:
            # Code example
            try:
                self.example = syntax['content']['CSharp']
            except KeyError:
                pass

            self.parameters = []
            for param in syntax.get('parameters', []):
                if 'id' in param:
                    self.parameters.append({
                        'name': param.get('id'),
                        'type': param.get('type', {}).get('id', None),
                        'desc': param.get('description', '')
                    })

        self.children = obj.get('items', [])
        if self.children:
            self.item_map = defaultdict(list)
            self.sort()

    @property
    def ref_type(self):
        return self.type.lower().replace('class', 'cls').replace('interface', 'iface').replace('delegate', 'del')

    def to_ref_type(self, _type):
        return _type.lower().replace('class', 'cls').replace('interface', 'iface').replace('delegate', 'del')

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


class VirtualNamespace(AutoAPIBase):
    language = 'dotnet'
    type = 'namespace'

    def __init__(self, name, objs):
        self.name = self.short_name = name
        self.children = []
        self.type = 'namespace'
        for obj in objs:
            self.children.append(obj.obj)
