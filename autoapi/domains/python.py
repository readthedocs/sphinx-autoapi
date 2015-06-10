from collections import defaultdict

from epyparse import parsed

from .base import PythonMapperBase, SphinxMapperBase


class PythonDomain(SphinxMapperBase):

    '''Auto API domain handler for Python

    Parses directly from Python files.

    :param app: Sphinx application passed in as part of the extension
    '''

    def read_file(self, path, **kwargs):
        '''Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        '''
        # TODO support JSON here
        # TODO sphinx way of reporting errors in logs?

        try:
            parsed_data = parsed(path)
            return parsed_data
        except IOError:
            self.app.warn('Error reading file: {0}'.format(path))
        except TypeError:
            self.app.warn('Error reading file: {0}'.format(path))
        return None

    def create_class(self, data, **kwargs):
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
            obj = cls(data, jinja_env=self.jinja_env)
            if 'children' in data:
                for child_data in data['children']:
                    for child_obj in self.create_class(child_data):
                        obj.children.append(child_obj)
                        self.add_object(child_obj)
            yield obj


class PythonBase(PythonMapperBase):

    language = 'python'

    def __init__(self, obj, **kwargs):
        super(PythonBase, self).__init__(obj, **kwargs)

        # Always exist
        self.id = obj['fullname']
        self.name = self.obj.get('fullname', self.id)

        # Optional
        self.imports = obj.get('imports', [])
        self.children = []
        self.parameters = obj.get('params', [])
        self.docstring = obj.get('docstring', '')
        self.methods = obj.get('methods', [])

        # For later
        self.item_map = defaultdict(list)


class PythonFunction(PythonBase):
    type = 'function'


class PythonModule(PythonBase):
    type = 'module'
    top_level_object = True


class PythonClass(PythonBase):
    type = 'class'
