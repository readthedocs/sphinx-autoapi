import os
import textwrap
from collections import defaultdict
from pydocstyle.parser import Parser

from .base import PythonMapperBase, SphinxMapperBase
from ..utils import slugify


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
            parsed_data = Parser()(open(path), path)
            return parsed_data
        except IOError:
            self.app.warn('Error reading file: {0}'.format(path))
        except TypeError:
            self.app.warn('Error reading file: {0}'.format(path))
        except ImportError:
            self.app.warn('Error reading file: {0}'.format(path))
        return None

    def create_class(self, data, options=None, **kwargs):
        """Create a class from the passed in data

        :param data: dictionary data of pydocstyle output
        """
        obj_map = dict((cls.type, cls) for cls
                       in [PythonClass, PythonFunction, PythonModule, PythonMethod, PythonPackage])
        try:
            cls = obj_map[data.kind]
        except KeyError:
            self.app.warn("Unknown Type: %s" % data.kind)
        else:
            path = kwargs.get('path')
            obj = cls(data, jinja_env=self.jinja_env,
                      options=self.app.config.autoapi_options, path=path
                      )
            for child_data in data.children:
                for child_obj in self.create_class(child_data, options=options, path=path):
                    obj.children.append(child_obj)
                    self.add_object(child_obj)
            yield obj


class PythonPythonMapper(PythonMapperBase):

    language = 'python'

    def __init__(self, obj, **kwargs):
        super(PythonPythonMapper, self).__init__(obj, **kwargs)

        # Properly name the object with dot notation
        if self.top_level_object:
            name = self.path.relative.split('.')[0].replace('/', '.')
        else:
            name = '.'.join([
                os.path.dirname(self.path.relative).replace('/', '.'),
                obj.name
            ])
        self.id = slugify(name)
        self.name = name

        # Optional
        self.children = []
        try:
            args = obj.source.split('\n')[0]
            args = args.split('(')[1]
            args = args.split(')')[0]
            self.args = args.split(',')
        except:
            args = ''
        self.docstring = obj.docstring or ''
        self.docstring = textwrap.dedent(self.docstring)
        self.docstring = self.docstring.replace("'''", '').replace('"""', '')
        if getattr(obj, 'parent'):
            self.inheritance = [obj.parent.name]
        else:
            self.inheritance = ''

        # For later
        self.item_map = defaultdict(list)

    def __repr__(self):
        return 'Python {type}: {name}'.format(name=self.name, type=self.type)

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


class PythonMethod(PythonPythonMapper):
    type = 'method'


class PythonModule(PythonPythonMapper):
    type = 'module'
    top_level_object = True


class PythonPackage(PythonPythonMapper):
    type = 'package'
    top_level_object = True


class PythonClass(PythonPythonMapper):
    type = 'class'
