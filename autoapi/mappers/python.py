import sys
import os
import textwrap
import ast
from collections import defaultdict
from pydocstyle.parser import Parser

from .base import PythonMapperBase, SphinxMapperBase
from ..utils import slugify

if sys.version_info < (3,):
    from itertools import izip_longest as zip_longest
else:
    from itertools import zip_longest


class PythonSphinxMapper(SphinxMapperBase):

    """Auto API domain handler for Python

    Parses directly from Python files.

    :param app: Sphinx application passed in as part of the extension
    """

    def load(self, patterns, dirs, **kwargs):
        """Load objects from the filesystem into the ``paths`` dictionary

        Also include an attribute on the object, ``relative_path`` which is the
        shortened, relative path the package/module
        """
        for dir_ in dirs:
            for path in self.find_files(patterns=patterns, dirs=[dir_], **kwargs):
                data = self.read_file(path=path)
                data.relative_path = os.path.relpath(path, dir_)
                if data:
                    self.paths[path] = data

    def read_file(self, path, **kwargs):
        """Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        """
        try:
            parsed_data = Parser()(open(path), path)
            return parsed_data
        except (IOError, TypeError, ImportError):
            self.app.warn('Error reading file: {0}'.format(path))
        return None

    def create_class(self, data, options=None, path=None, **kwargs):
        """Create a class from the passed in data

        :param data: dictionary data of pydocstyle output
        """
        obj_map = dict((cls.type, cls) for cls
                       in [PythonClass, PythonFunction, PythonModule,
                           PythonMethod, PythonPackage])
        try:
            cls = obj_map[data.kind]
        except KeyError:
            self.app.warn("Unknown type: %s" % data.kind)
        else:
            obj = cls(data, jinja_env=self.jinja_env,
                      options=self.app.config.autoapi_options, **kwargs)
            for child_data in data.children:
                for child_obj in self.create_class(child_data, options=options,
                                                   **kwargs):
                    obj.children.append(child_obj)
            yield obj


class PythonPythonMapper(PythonMapperBase):

    language = 'python'
    is_callable = False

    def __init__(self, obj, **kwargs):
        super(PythonPythonMapper, self).__init__(obj, **kwargs)

        self.name = self._get_full_name(obj)
        self.id = slugify(self.name)

        # Optional
        self.children = []
        self.args = []
        if self.is_callable:
            self.args = self._get_arguments(obj)
        self.docstring = obj.docstring or ''
        self.docstring = textwrap.dedent(self.docstring)
        self.docstring = self.docstring.replace("'''", '').replace('"""', '')
        if getattr(obj, 'parent'):
            self.inheritance = [obj.parent.name]
        else:
            self.inheritance = []

        # For later
        self.item_map = defaultdict(list)

    @property
    def is_undoc_member(self):
        return self.docstring == ''

    @property
    def is_private_member(self):
        return self.short_name[0] == '_'

    @property
    def is_special_member(self):
        return self.short_name[0:2] == '__'

    @property
    def display(self):
        if self.is_undoc_member and 'undoc-members' not in self.options:
            return False
        if self.is_private_member and 'private-members' not in self.options:
            return False
        if self.is_special_member and 'special-members' not in self.options:
            return False
        return True

    @staticmethod
    def _get_full_name(obj):
        """Recursively build the full name of the object from pydocstyle

        Uses an additional attribute added to the object, ``relative_path``.
        This is the shortened path of the object name, if the object is a
        package or module.

        :param obj: pydocstyle object, as returned from Parser()
        :returns: Dotted name of object
        :rtype: str
        """

        def _inner(obj, parts=None):
            if parts is None:
                parts = []
            obj_kind = obj.kind
            obj_name = obj.name
            if obj_kind == 'module':
                obj_name = getattr(obj, 'relative_path', None) or obj.name
                obj_name = obj_name.replace('/', '.')
                ext = '.py'
                if obj_name.endswith(ext):
                    obj_name = obj_name[:-len(ext)]
            elif obj_kind == 'package':
                obj_name = getattr(obj, 'relative_path', None) or obj.name
                exts = ['/__init__.py', '.py']
                for ext in exts:
                    if obj_name.endswith(ext):
                        obj_name = obj_name[:-len(ext)]
                obj_name = obj_name.split('/').pop()
            parts.insert(0, obj_name)
            try:
                return _inner(obj.parent, parts)
            except AttributeError:
                pass
            return parts

        return '.'.join(_inner(obj))

    @staticmethod
    def _get_arguments(obj):
        """Get arguments from a pydocstyle object

        :param obj: pydocstyle object, as returned from Parser()
        :returns: list of argument or argument and value pairs
        :rtype: list
        """
        def get_arg_names(args):
            """Get the names of each ast-parsed argument in the given list.

            :param list(ast.Name or ast.Tuple) args: The list of ast-parsed
                arguments to get names for.
            :returns: The names of the given arguments.
            :rtype: generator(str)
            """
            for arg in args:
                if isinstance(arg, ast.Tuple):
                    for name in get_arg_names(arg.elts):
                        yield name
                elif sys.version_info < (3,):
                    yield arg.id
                else:
                    yield arg.arg

        arguments = []
        source = textwrap.dedent(obj.source)
        # Bare except here because AST parsing can throw any number of
        # exceptions, including SyntaxError
        try:
            parsed = ast.parse(source)
        except Exception as e:  # noqa
            print("Error parsing AST: %s" % str(e))
            return []
        parsed_args = parsed.body[0].args
        arg_names = list(get_arg_names(parsed_args.args))

        # Get defaults for display based on AST node type
        arg_defaults = []
        pydocstyle_map = {
            ast.Name: 'id',
            ast.Num: 'n',
            ast.Str: lambda obj: '"{0}"'.format(obj.s),
            ast.Call: lambda obj: obj.func.id,
            # TODO these require traversal into the AST nodes. Add this for more
            # complete argument parsing, or handle with a custom AST traversal.
            ast.List: lambda _: 'list',
            ast.Tuple: lambda _: 'tuple',
            ast.Set: lambda _: 'set',
            ast.Dict: lambda _: 'dict',
        }
        if sys.version_info >= (3,):
            pydocstyle_map.update({
                ast.NameConstant: 'value',
            })

        for value in parsed_args.defaults:
            default = None
            try:
                default = pydocstyle_map[type(value)](value)
            except TypeError:
                default = getattr(value, pydocstyle_map[type(value)])
            except KeyError:
                pass
            if default is None:
                default = 'None'
            arg_defaults.append(default)

        # Apply defaults padded to the end of the longest list. AST returns
        # argument defaults as a short array that applies to the end of the list
        # of arguments
        for (name, default) in zip_longest(reversed(arg_names),
                                           reversed(arg_defaults)):
            arg = name
            if default is not None:
                arg = '{0}={1}'.format(name, default)
            arguments.insert(0, arg)

        # Add *args and **kwargs
        if parsed_args.vararg:
            arguments.append('*{0}'.format(
                parsed_args.vararg
                if sys.version_info < (3, 3)
                else parsed_args.vararg.arg
            ))
        if parsed_args.kwarg:
            arguments.append('**{0}'.format(
                parsed_args.kwarg
                if sys.version_info < (3, 3)
                else parsed_args.kwarg.arg
            ))

        return arguments


class PythonFunction(PythonPythonMapper):
    type = 'function'
    is_callable = True


class PythonMethod(PythonPythonMapper):
    type = 'method'
    is_callable = True


class PythonModule(PythonPythonMapper):
    type = 'module'
    top_level_object = True


class PythonPackage(PythonPythonMapper):
    type = 'package'
    top_level_object = True


class PythonClass(PythonPythonMapper):
    type = 'class'
