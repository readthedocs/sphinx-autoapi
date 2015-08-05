from collections import defaultdict
import sys

from .base import PythonMapperBase, SphinxMapperBase

if sys.version_info < (3,):
    from epyparse import parsed
else:
    # Don't raise exception on module level because it would
    # break all backends on Python 3
    def parsed(path):
        raise Exception('Python 3 not supported')


class PythonSphinxMapper(SphinxMapperBase):

    '''Auto API domain handler for Python

    Parses directly from Python files.

    :param app: Sphinx application passed in as part of the extension
    '''

    def read_file(self, path, **kwargs):
        '''Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        '''

        try:
            parsed_data = parsed(path)
            return parsed_data
        except IOError:
            self.app.warn('Error reading file: {0}'.format(path))
        except TypeError:
            self.app.warn('Error reading file: {0}'.format(path))
        except ImportError:
            self.app.warn('Error reading file: {0}'.format(path))
        return None

    def create_class(self, data, options=None, **kwargs):
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
            obj = cls(data, jinja_env=self.jinja_env, options=self.app.config.autoapi_options)
            if 'children' in data:
                for child_data in data['children']:
                    for child_obj in self.create_class(child_data, options=options):
                        obj.children.append(child_obj)
                        self.add_object(child_obj)
            yield obj


class PythonPythonMapper(PythonMapperBase):

    language = 'python'

    def __init__(self, obj, **kwargs):
        super(PythonPythonMapper, self).__init__(obj, **kwargs)

        # Always exist
        self.id = obj['fullname']
        self.name = self.obj.get('fullname', self.id)

        # Optional
        self.imports = obj.get('imports', [])
        self.children = []
        self.args = obj.get('args', [])
        self.params = obj.get('params', [])
        self.docstring = obj.get('docstring', '')
        self.methods = obj.get('methods', [])
        self.inheritance = obj.get('bases', [])

        # For later
        self.item_map = defaultdict(list)

    @property
    def undoc_member(self):
        return self.docstring == ''

    @property
    def private_member(self):
        return self.short_name[0] == '_'

    @property
    def special_member(self):
        return self.short_name[0:2] == '__'

    @property
    def display(self):
        if self.undoc_member and 'undoc-members' not in self.options:
            return False
        if self.private_member and 'private-members' not in self.options:
            return False
        if self.special_member and 'special-members' not in self.options:
            return False
        return True


class PythonFunction(PythonPythonMapper):
    type = 'function'


class PythonModule(PythonPythonMapper):
    type = 'module'
    top_level_object = True


class PythonClass(PythonPythonMapper):
    type = 'class'
