import os
from collections import defaultdict
import json

from sphinx.util.osutil import ensuredir

from ..base import AutoAPIBase, AutoAPIDomain
from ..settings import env


class GoDomain(AutoAPIDomain):

    '''Auto API domain handler for Go

    Parses directly from Go files.

    :param app: Sphinx application passed in as part of the extension
    '''

    # def read_file(self, path, format=None):
    #     '''Read file input into memory, returning deserialized objects

    #     :param path: Path of file to read
    #     '''
    # TODO support JSON here
    # TODO sphinx way of reporting errors in logs?

    #     try:
    #         raw_json = os.system('godocjson %s' % path)
    #         parsed_data = json.loads(raw_json)
    #         return parsed_data
    #     except IOError:
    #         print Warning('Error reading file: {0}'.format(path))
    #     except TypeError:
    #         print Warning('Error reading file: {0}'.format(path))
    #     return None

    def create_class(self, data, _type=None):
        '''Return instance of class based on Go data

        Data keys handled here:

            type
                Set the object class

            items
                Recurse into :py:meth:`create_class` to create child object
                instances

        :param data: dictionary data from Roslyn output artifact
        '''
        # TODO replace this with a global mapping
        classes = [GoConstant, GoFunction, GoPackage, GoVariable, GoType, GoMethod]
        obj = None
        if not _type:
            _type = data.get('type', '').lower()
        for cls in classes:
            if _type == cls.type.lower():
                obj = cls(data)
        if not obj:
            print "Unknown Type: %s" % data

        for child_type in ['consts', 'types', 'vars', 'funcs']:
            # if child_type == 'consts' or child_type == 'vars':
            #     iter_data = []
            #     for inner_data in data.get(child_type, []):
            #         for name in inner_data.get('name', [])
            #         del inner_data['doc']
            #         iter_data.append({
            #             'name': name,
            #             **inner_data
            #             })
            # else:
            iter_data = data.get(child_type, [])
            for obj_data in iter_data:
                child_obj = self.create_class(obj_data, _type=child_type.replace('consts', 'const').replace('types', 'type').replace('vars', 'variable').replace('funcs', 'func'))
                obj.children.append(child_obj)
                obj.item_map[child_obj.type].append(child_obj)
        return obj

    def organize_objects(self):
        '''Organize objects and namespaces'''

        # Add all objects to the item_map
        for obj in self.objects.values():
            for child in obj.children:
                child_object = self.objects.get(child)
                if child_object:
                    obj.children.append(child_object)
            # for key in obj.item_map:
            #     obj.item_map[key].sort()

    def full(self):
        print "Reading"
        self.get_objects(self.get_config('autoapi_file_pattern'), format='json')
        # self.organize_objects()
        print "Writing"
        self.generate_output()
        self.write_indexes()

    def generate_output(self):
        for obj in self.app.env.autoapi_data:

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

    def write_indexes(self):
        # Write Index
        top_level_index = os.path.join(self.get_config('autoapi_root'),
                                       'index.rst')
        with open(top_level_index, 'w+') as top_level_file:
            content = env.get_template('index.rst')
            top_level_file.write(content.render())


class GoBase(AutoAPIBase):

    language = 'go'

    def __init__(self, obj):
        super(GoBase, self).__init__(obj)
        # Always exist
        #self.id = obj['import_path']
        try:
            self.name = obj['name']
        except:
            self.name = obj['packageName']
        try:
            self.id = obj['packageImportPath']
        except:
            self.id = self.name

        # Second level
        self.imports = obj.get('imports', [])
        self.children = []
        self.parameters = obj.get('params', [])
        self.docstring = obj.get('doc', '')

        # Go Specific
        self.notes = obj.get('notes', {})
        self.filenames = obj.get('filenames', [])
        self.bugs = obj.get('bugs', [])

        # For later
        self.item_map = defaultdict(list)

    def __str__(self):
        return '<{cls} {id}>'.format(cls=self.__class__.__name__,
                                     id=self.id)

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


class GoVariable(GoBase):
    type = 'variable'
    ref_type = 'var'


class GoMethod(GoBase):
    type = 'method'


class GoConstant(GoBase):
    type = 'const'


class GoFunction(GoBase):
    type = 'func'
    ref_type = 'function'


class GoPackage(GoBase):
    type = 'package'


class GoType(GoBase):
    type = 'type'
