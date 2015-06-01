import os
import sys
from collections import defaultdict

from sphinx.util.osutil import ensuredir
from epyparse import parsed

from ..base import AutoAPIBase, AutoAPIDomain
from ..settings import env


class PythonDomain(AutoAPIDomain):

    '''Auto API domain handler for Python

    Parses directly from Python files.

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

        :param data: dictionary data of epydoc output
        '''
        obj_map = dict((cls.type, cls) for cls
                       in [PythonClass, PythonFunction, PythonModule])
        try:
            cls = obj_map[data['type']]
        except KeyError:
            self.app.warn("Unknown Type: %s" % data['type'])
        else:
            obj = cls(data)
            if 'children' in data:
                for child_data in data['children']:
                    child_obj = self.create_class(child_data)
                    obj.children.append(child_obj)
            yield obj

    def read_file(self, path):
        '''Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        '''
        # TODO support JSON here
        # TODO sphinx way of reporting errors in logs?

        try:
            parsed_data = parsed(path)
            return parsed_data
        except IOError:
            print Warning('Error reading file: {0}'.format(path))
        except TypeError:
            print Warning('Error reading file: {0}'.format(path))
        return None

    def get_objects(self, pattern):
        '''Trigger find of serialized sources and build objects'''
        for path in self.find_files(pattern):
            data = self.read_file(path)
            if data:
                obj = self.create_class(data)
                self.add_object(obj)

    def add_object(self, obj):
        '''Add object to local and app environment storage

        :param obj: Instance of a AutoAPI object
        '''
        self.app.env.autoapi_data.append(obj)
        self.objects[obj.name] = obj

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
                            isinstance(search_obj, PythonModule)):
                        ns_obj = self.app.env.autoapi_data[n]
                if ns_obj is None:
                    ns_obj = self.create_class({'id': namespace,
                                                'type': 'module'})
                    self.app.env.autoapi_data.append(ns_obj)
                    self.namespaces[ns_obj.id] = ns_obj
                if obj.id not in (child.id for child in ns_obj.children):
                    ns_obj.children.append(obj)
                _recurse_ns(ns_obj)

        for obj in self.app.env.autoapi_data:
            _recurse_ns(obj)

    def full(self):
        print "Reading"
        self.get_objects(self.get_config('autoapi_file_pattern'))
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
                    detail_file.write(rst)

    def write_indexes(self):
        # Write Index
        top_level_index = os.path.join(self.get_config('autoapi_root'),
                                       'index.rst')
        with open(top_level_index, 'w+') as top_level_file:
            content = env.get_template('index.rst')
            top_level_file.write(content.render())


class PythonBase(AutoAPIBase):

    language = 'python'

    def __init__(self, obj):
        super(PythonBase, self).__init__(obj)
        # Always exist
        self.id = obj['fullname']

        # Optional
        self.imports = obj.get('imports', [])
        self.children = []
        self.parameters = obj.get('params', [])
        self.docstring = obj.get('docstring', '')

        # For later
        self.item_map = defaultdict(list)

    def __str__(self):
        return '<{cls} {id}>'.format(cls=self.__class__.__name__,
                                     id=self.id)

    @property
    def name(self):
        '''Return short name for member id

        '''
        try:
            return self.obj['fullname']
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

    @property
    def methods(self):
        return self.obj.get('methods', [])


class PythonFunction(PythonBase):
    type = 'function'


class PythonModule(PythonBase):
    type = 'module'


class PythonClass(PythonBase):
    type = 'class'
