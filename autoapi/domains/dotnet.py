import os
from collections import defaultdict

from sphinx.util.osutil import ensuredir

from .base import AutoAPIBase, AutoAPIDomain
from ..settings import env

MADE = set()


class DotNetDomain(AutoAPIDomain):

    '''Auto API domain handler for .NET

    Searches for YAML files, and soon to be JSON files as well, for auto API
    sources

    :param app: Sphinx application passed in as part of the extension
    '''

    top_namespaces = {}

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
        obj_map = dict(
            (cls.type, cls) for cls
            in [
                DotNetNamespace, DotNetClass, DotNetEnum, DotNetStruct,
                DotNetInterface, DotNetDelegate, DotNetProperty, DotNetMethod,
                DotNetConstructor, DotNetField, DotNetEvent
            ])
        try:
            cls = obj_map[data['type'].lower()]
        except KeyError:
            self.app.warn('Unknown type: %s' % data)
        else:
            obj = cls(data)

            # TODO what is MADE?
            if data.get('id', None) in MADE:
                self.app.warn("Object already added: %s" % data.get('id'))
            MADE.add(data['id'])

            # Append child objects
            # TODO this should recurse in the case we're getting back more
            # complex argument listings
            # if 'children' in data:
            #     for item in data['children']:
            #         child_obj = self.create_class(item)
            #         obj.children.append(child_obj)

            yield obj

    def get_objects(self, pattern):
        '''Trigger find of serialized sources and build objects'''
        for path in self.find_files(pattern):
            data_objects = self.read_file(path)
            if type(data_objects) == dict:
                data_objects = data_objects['items']
            try:
                for data in data_objects:
                    for obj in self.create_class(data):
                        self.add_object(obj)
            except:
                import traceback
                traceback.print_exc()

    def add_object(self, obj):
        '''Add object to local and app environment storage

        :param obj: Instance of a .NET object
        '''
        if obj.top_level_object:
            self.top_level_objects[obj.name] = obj
            if type(obj) == DotNetNamespace:
                self.namespaces[obj.name] = obj
        self.objects[obj.id] = obj

    def organize_objects(self):
        '''Organize objects and namespaces'''

        def _render_children(obj):
            for child in obj.children_strings:
                child_object = self.objects.get(child)
                if child_object:
                    obj.item_map[child_object.plural].append(child_object)
                    obj.children.append(child_object)
            for key in obj.item_map:
                obj.item_map[key].sort()

        def _recurse_ns(obj):
            if not obj:
                return
            namespace = obj.top_namespace
            if namespace is not None:
                ns_obj = self.top_namespaces.get(namespace)
                if ns_obj is None or type(ns_obj) != DotNetNamespace:
                    print "Adding Namespace %s" % namespace
                    for ns_obj in self.create_class({'id': namespace,
                                                     'type': 'namespace'}):
                        self.top_namespaces[ns_obj.id] = ns_obj
                if obj not in ns_obj.children and namespace != obj.id:
                    ns_obj.children.append(obj)

        for obj in self.top_level_objects.values():
            _render_children(obj)
            _recurse_ns(obj)

        # Clean out dead namespaces
        for key, ns in self.top_namespaces.items():
            if len(ns.children) == 0:
                del self.top_namespaces[key]

        for key, ns in self.namespaces.items():
            if len(ns.children) == 0:
                del self.namespaces[key]

    def full(self):
        print "Reading"
        self.get_objects(self.get_config('autoapi_file_pattern'))
        self.organize_objects()

        print "Writing"
        self.generate_output()
        self.write_indexes()

    def generate_output(self):
        for obj in self.top_level_objects.values():

            if not obj:
                continue


            rst = obj.render()
            # Detail
            try:
                filename = obj.name.split('(')[0]
            except IndexError:
                filename = obj.name
            detail_dir = os.path.join(self.get_config('autoapi_root'),
                                      *filename.split('.'))
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
            top_level_file.write(content.render(pages=self.namespaces.values()))


class DotNetBase(AutoAPIBase):

    '''Base .NET object representation'''

    language = 'dotnet'
    top_level_object = False

    def __init__(self, obj):
        super(DotNetBase, self).__init__(obj)
        # Always exist
        self.id = obj['id']

        # Optional
        self.fullname = obj.get('fullName')
        self.summary = obj.get('summary', '')
        self.parameters = []
        self.items = obj.get('items', [])
        self.children_strings = obj.get('children', [])
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
            return self.obj['fullName']
        except KeyError:
            return self.id

    @property
    def short_name(self):
        '''Shorten name property'''
        return self.name.split('.')[-1]

    @property
    def edit_link(self):
        try:
            repo = self.source['remote']['repo'].replace('.git', '')
            path = self.path
            return '{repo}/blob/master/{path}'.format(
                repo=repo,
                path=path,
                )
        except:
            import traceback; traceback.print_exc();
            return ''

    @property
    def source(self):
        return self.obj.get('source')

    @property
    def path(self):
        return self.source['path']

    @property
    def namespace(self):
        pieces = self.id.split('.')[:-1]
        if pieces:
            return '.'.join(pieces)

    @property
    def top_namespace(self):
        pieces = self.id.split('.')[:2]
        if pieces:
            return '.'.join(pieces)

    @property
    def ref_type(self):
        return self.type

    @property
    def ref_directive(self):
        return self.type

    @property
    def ref_name(self):
        '''Return object name suitable for use in references

        Escapes several known strings that cause problems, including the
        following reference syntax::

            :dotnet:cls:`Foo.Bar<T>`

        As the `<T>` notation is also special syntax in references, indicating
        the reference to Foo.Bar should be named T.

        See: http://sphinx-doc.org/domains.html#role-cpp:any
        '''
        return (self.name
                .replace('<', '\<')
                .replace('`', '\`'))

    @property
    def ref_short_name(self):
        '''Same as above, return the truncated name instead'''
        return self.ref_name.split('.')[-1]


class DotNetNamespace(DotNetBase):
    type = 'namespace'
    ref_directive = 'ns'
    plural = 'namespaces'
    top_level_object = True


class DotNetMethod(DotNetBase):
    type = 'method'
    ref_directive = 'meth'
    plural = 'methods'


class DotNetProperty(DotNetBase):
    type = 'property'
    ref_directive = 'prop'
    plural = 'properties'


class DotNetEnum(DotNetBase):
    type = 'enum'
    ref_type = 'enumeration'
    ref_directive = 'enum'
    plural = 'enumerations'
    top_level_object = True


class DotNetStruct(DotNetBase):
    type = 'struct'
    ref_type = 'structure'
    ref_directive = 'struct'
    plural = 'structures'
    top_level_object = True


class DotNetConstructor(DotNetBase):
    type = 'constructor'
    ref_directive = 'ctor'
    plural = 'constructors'


class DotNetInterface(DotNetBase):
    type = 'interface'
    ref_directive = 'iface'
    plural = 'interfaces'
    top_level_object = True


class DotNetDelegate(DotNetBase):
    type = 'delegate'
    ref_directive = 'del'
    plural = 'delegates'
    top_level_object = True


class DotNetClass(DotNetBase):
    type = 'class'
    ref_directive = 'cls'
    plural = 'classes'
    top_level_object = True


class DotNetField(DotNetBase):
    type = 'field'
    plural = 'fields'


class DotNetEvent(DotNetBase):
    type = 'event'
    plural = 'events'
