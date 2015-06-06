import os
import json
import subprocess

from sphinx.util.osutil import ensuredir

from .base import AutoAPIBase, AutoAPIDomain
from ..settings import env


class JavaScriptDomain(AutoAPIDomain):

    '''Auto API domain handler for Javascript

    Parses directly from Javascript files.

    :param app: Sphinx application passed in as part of the extension
    '''

    def create_class(self, data):
        '''Return instance of class based on Javascript data

        Data keys handled here:

            type
                Set the object class

            consts, types, vars, funcs
                Recurse into :py:meth:`create_class` to create child object
                instances

        :param data: dictionary data from godocjson output
        '''
        obj_map = dict(
            (cls.type, cls) for cls
            in ALL_CLASSES
        )
        try:
            cls = obj_map[data['kind']]
        except KeyError:
            self.app.warn('Unknown Type: %s' % data)
        else:
            # Recurse for children
            obj = cls(data)
            if 'children' in data:
                for child_data in data['children']:
                    for child_obj in self.create_class(child_data):
                        obj.children.append(child_obj)
            yield obj

    def read_file(self, path, **kwargs):
        '''Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        '''
        # TODO support JSON here
        # TODO sphinx way of reporting errors in logs?

        try:
            parsed_data = json.loads(subprocess.check_output(['jsdoc', '-X', path]))
            return parsed_data
        except IOError:
            print Warning('Error reading file: {0}'.format(path))
        except TypeError:
            print Warning('Error reading file: {0}'.format(path))
        return None

    def get_objects(self, pattern, format='yaml'):
        '''Trigger find of serialized sources and build objects'''
        for path in self.find_files(pattern):
            data = self.read_file(path, format=format)
            if data:
                # Returns a list of objects
                for item in data:
                    for obj in self.create_class(item):
                        self.add_object(obj)

    def full(self):
        self.get_objects(self.get_config('autoapi_file_pattern'), format='json')
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


class JavaScriptBase(AutoAPIBase):

    language = 'javascript'

    def __init__(self, obj):
        super(JavaScriptBase, self).__init__(obj)
        self.name = obj.get('name')
        self.id = self.name

        # Second level
        self.docstring = obj.get('description', '')
        #self.docstring = obj.get('comment', '')

        self.imports = obj.get('imports', [])
        self.children = []
        self.parameters = map(
            lambda n: {'name': n['name'],
                       'type': n['type'][0]},
            obj.get('param', [])
        )

        # Language Specific
        pass


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


class JavaScriptClass(JavaScriptBase):
    type = 'class'
    ref_directive = 'class'


class JavaScriptFunction(JavaScriptBase):
    type = 'function'
    ref_type = 'func'


class JavaScriptData(JavaScriptBase):
    type = 'data'
    ref_directive = 'data'


class JavaScriptMember(JavaScriptBase):
    type = 'member'
    ref_directive = 'member'


class JavaScriptAttribute(JavaScriptBase):
    type = 'attribute'
    ref_directive = 'attr'

ALL_CLASSES = [
    JavaScriptFunction,
    JavaScriptClass,
    JavaScriptData,
    JavaScriptAttribute,
    JavaScriptMember,
]
