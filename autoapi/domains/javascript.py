import os
import json
import subprocess


from .base import AutoAPIBase, AutoAPIDomain


class JavaScriptDomain(AutoAPIDomain):

    '''Auto API domain handler for Javascript

    Parses directly from Javascript files.

    :param app: Sphinx application passed in as part of the extension
    '''

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
            self.app.warn('Error reading file: {0}'.format(path))
        except TypeError:
            self.app.warn('Error reading file: {0}'.format(path))
        return None

    def map(self):
        '''Trigger find of serialized sources and build objects'''
        for path, data in self.paths.items():
            for item in data:
                for obj in self.create_class(item):
                    obj.jinja_env = self.jinja_env
                    self.add_object(obj)

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


class JavaScriptBase(AutoAPIBase):

    language = 'javascript'

    def __init__(self, obj):
        '''
        Map JSON data into Python object.

        This is the standard object that will be rendered into the templates,
        so we try and keep standard naming to keep templates more re-usable.
        '''

        super(JavaScriptBase, self).__init__(obj)
        self.name = obj.get('name')
        self.id = self.name

        # Second level
        self.docstring = obj.get('description', '')
        # self.docstring = obj.get('comment', '')

        self.imports = obj.get('imports', [])
        self.children = []
        self.parameters = map(
            lambda n: {'name': n['name'],
                       'type': n['type'][0]},
            obj.get('param', [])
        )

        # Language Specific
        pass


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
