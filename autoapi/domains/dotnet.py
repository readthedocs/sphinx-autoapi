import os
from collections import defaultdict

from sphinx.util.console import bold, darkgreen
from sphinx.util.osutil import ensuredir

from ..base import AutoAPIBase, AutoAPIDomain
from ..settings import env


class DotNetDomain(AutoAPIDomain):
    '''Auto API domain handler for .NET

    Searches for YAML files, and soon to be JSON files as well, for auto API
    sources

    :param app: Sphinx application passed in as part of the extension
    '''

    def create_class(self, data):
        '''Return instance of class based on Roslyn type property

        Data keys handled here:

            type
                Set the object class

            items
                Recurse into :py:meth:`create_class` to create child object
                instances

        :param data: dictionary data from Roslyn output artifact
        '''
        # TODO replace this with a global mapping
        classes = [DotNetNamespace, DotNetClass, DotNetProperty, DotNetMethod,
                   DotNetEnum, DotNetConstructor, DotNetStruct, DotNetInterface,
                   DotNetDelegate, DotNetField, DotNetEvent]
        obj = None
        for cls in classes:
            if data.get('type', '').lower() == cls.type.lower():
                obj = cls(data)

        # Append child objects
        # TODO this should recurse in the case we're getting back more complex
        # argument listings
        if 'items' in data:
            for item in data['items']:
                child_obj = self.create_class(item)
                obj.children.append(child_obj)

        return obj

    def get_objects(self):
        '''Trigger find of serialized sources and build objects'''
        for path in self.find_files():
            data = self.read_file(path)
            try:
                obj = self.create_class(data)
                self.add_object(obj)
            except:
                import traceback; traceback.print_exc();

    def add_object(self, obj):
        '''Add object to local and app environment storage

        :param obj: Instance of a .NET object
        '''
        self.app.env.autoapi_data.append(obj)
        self.objects.append(obj)

    def organize_objects(self):
        '''Organize objects and namespaces'''

        def _recurse_ns(obj):
            if not obj:
                return
            namespace = obj.namespace
            if namespace is not None:
                ns_obj = None
                for (n, search_obj) in enumerate(self.app.env.autoapi_data):
                    if (search_obj.id == namespace and
                            isinstance(search_obj, DotNetNamespace)):
                        ns_obj = self.app.env.autoapi_data[n]
                if ns_obj is None:
                    ns_obj = self.create_class({'id': namespace,
                                                'type': 'namespace'})
                    self.app.env.autoapi_data.append(ns_obj)
                    self.namespaces[ns_obj.id] = ns_obj
                if obj.id not in (child.id for child in ns_obj.children):
                    ns_obj.children.append(obj)
                _recurse_ns(ns_obj)

        for obj in self.app.env.autoapi_data:
            _recurse_ns(obj)

    def full(self):
        print "Reading"
        self.get_objects()
        self.organize_objects()
        print "Writing"
        self.generate_output()
        self.write_indexes()

    def generate_output(self):
        for obj in self.app.env.autoapi_data:
            # TODO not here!
            for child in obj.children:
                obj.item_map[child.type].append(child)
            for key in obj.item_map.keys():
                obj.item_map[key].sort()

            rst = obj.render()
            # Detail
            detail_dir = os.path.join(self.get_config('autoapi_root'),
                                      *obj.name.split('.'))
            ensuredir(detail_dir)
            # TODO: Better way to determine suffix?
            path = os.path.join(detail_dir, '%s%s' % ('index', self.get_config('source_suffix')[0]))
            if rst:
                with open(path, 'w+') as detail_file:
                    detail_file.write(rst.encode('utf-8'))

        # for namespace, obj in self.namespaces.items():
        #     path = os.path.join(self.get_config('autoapi_root'), '%s%s' % (namespace, self.get_config('source_suffix')[0]))
        #     ensuredir(self.get_config('autoapi_root'))
        #     with open(path, 'w+') as index_file:
        #         namespace_rst = obj.render()
        #         if namespace_rst:
        #             index_file.write(namespace_rst)

    def write_indexes(self):
        # Write Index
        top_level_index = os.path.join(self.get_config('autoapi_root'),
                                       'index.rst')
        with open(top_level_index, 'w+') as top_level_file:
            content = env.get_template('index.rst')
            top_level_file.write(content.render())


class DotNetBase(AutoAPIBase):
    '''Base .NET object representation'''

    language = 'dotnet'

    def __init__(self, obj):
        super(DotNetBase, self).__init__(obj)
        # Always exist
        self.id = obj['id']

        # Optional
        self.summary = obj.get('summary', '')
        self.parameters = []
        self.items = obj.get('items', [])
        self.children = []
        self.item_map = defaultdict(list)
        self.inheritance = []

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

            self.returns = syntax.get('return', None)

        # Inheritance
        # TODO Support more than just a class type here, should support enum/etc
        self.inheritance = [DotNetClass({'id': iobj['id'], 'name': iobj['name']})
                            for iobj in obj.get('inheritance', [])]

    def __str__(self):
        return '<{cls} {id}>'.format(cls=self.__class__.__name__,
                                     id=self.id)

    @property
    def name(self):
        '''Return short name for member id

        Use C# qualified name from deserialized data first, falling back to the
        member id minus the namespace prefix
        '''
        try:
            return self.obj['qualifiedName']['CSharp']
        except KeyError:
            return self.id

    @property
    def short_name(self):
        '''Shorten name property'''
        return self.name.split('.')[-1]

    @property
    def namespace(self):
        pieces = self.id.split('.')[:-1]
        if pieces:
            return '.'.join(pieces)

    @property
    def ref_type(self):
        return self.type

    @property
    def ref_directive(self):
        return self.type


class DotNetNamespace(DotNetBase):
    type = 'namespace'
    ref_directive = 'ns'


class DotNetMethod(DotNetBase):
    type = 'method'
    ref_directive = 'meth'


class DotNetProperty(DotNetBase):
    type = 'property'
    ref_directive = 'prop'


class DotNetEnum(DotNetBase):
    type = 'enum'
    ref_type = 'enumeration'
    ref_directive = 'enum'


class DotNetStruct(DotNetBase):
    type = 'struct'
    ref_type = 'structure'
    ref_directive = 'struct'


class DotNetConstructor(DotNetBase):
    type = 'constructor'
    ref_directive = 'ctor'


class DotNetInterface(DotNetBase):
    type = 'interface'
    ref_directive = 'iface'


class DotNetDelegate(DotNetBase):
    type = 'delegate'
    ref_directive = 'del'


class DotNetClass(DotNetBase):
    type = 'class'
    ref_directive = 'cls'


class DotNetField(DotNetBase):
    type = 'field'


class DotNetEvent(DotNetBase):
    type = 'event'


class DotNetVirtualNamespace(AutoAPIBase):
    language = 'dotnet'
    type = 'namespace'
    ref_type = 'ns'

    def __init__(self, name, objs):
        self.name = self.short_name = name
        self.children = []
        self.type = 'namespace'
        for obj in objs:
            self.children.append(obj.obj)
