import sys
import os
import textwrap
import ast
import tokenize as tk
from collections import defaultdict

from pydocstyle import parser

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

    def load(self, patterns, dirs, ignore=None):
        """Load objects from the filesystem into the ``paths`` dictionary

        Also include an attribute on the object, ``relative_path`` which is the
        shortened, relative path the package/module
        """
        for dir_ in dirs:
            for path in self.find_files(patterns=patterns, dirs=[dir_], ignore=ignore):
                data = self.read_file(path=path)
                data.relative_path = os.path.relpath(path, dir_)
                if data:
                    self.paths[path] = data

    def read_file(self, path, **kwargs):
        """Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        """
        try:
            parsed_data = ParserExtra()(open(path), path)
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
        self.docstring = obj.docstring
        if getattr(obj, 'parent'):
            self.inheritance = [obj.parent.name]
        else:
            self.inheritance = []

        # For later
        self.item_map = defaultdict(list)

    @property
    def is_undoc_member(self):
        return bool(self.docstring)

    @property
    def is_private_member(self):
        return not self.obj.is_public

    @property
    def is_special_member(self):
        return (
            (isinstance(self.obj, parser.Method) and self.obj.is_magic) or
            (self.obj.name.startswith('__') and self.obj.name.endswith('__'))
        )

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
                obj_name = obj_name.replace('/', '.')
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
        arg_names = [arg.id if sys.version_info < (3,) else arg.arg
                     for arg in parsed_args.args]

        # Get defaults for display based on AST node type
        arg_defaults = []
        pydocstyle_map = {
            ast.Name: 'id',
            ast.Num: 'n',
            ast.Str: lambda obj: '"{0}"'.format(obj.s),
            # Call function name can be an `Attribute` or `Name` node, make sure
            # we're using the correct attribute for the id
            ast.Call: lambda obj: (obj.func.id if isinstance(obj.func, ast.Name)
                                   else obj.func.attr),
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

    @property
    def summary(self):
        for line in self.docstring.splitlines():
            line = line.strip()
            if line:
                return line

        return ''


class PythonFunction(PythonPythonMapper):
    type = 'function'
    is_callable = True
    ref_directive = 'func'


class PythonMethod(PythonPythonMapper):
    type = 'method'
    is_callable = True
    ref_directive = 'meth'


class PythonModule(PythonPythonMapper):
    type = 'module'
    top_level_object = True


class PythonPackage(PythonPythonMapper):
    type = 'package'
    top_level_object = True


class PythonClass(PythonPythonMapper):
    type = 'class'


# Parser
class ParserExtra(parser.Parser):

    """Extend Parser object to provide customized return"""

    def parse_object_identifier(self):
        """Parse object identifier"""
        assert self.current.kind == tk.NAME
        identifier = ''
        while True:
            is_identifier = (
                self.current.kind == tk.NAME or
                (
                    self.current.kind == tk.OP and
                    self.current.value == '.'
                )
            )
            if is_identifier:
                identifier += self.current.value
                self.stream.move()
            else:
                break
        return identifier

    def parse_string(self):
        """Clean up STRING nodes"""
        val = self.current.value
        self.consume(tk.STRING)
        return val.lstrip('\'"').rstrip('\'"')

    def parse_number(self):
        """Parse a NUMBER node to either a ``float`` or ``int``"""
        val = self.current.value
        self.consume(tk.NUMBER)
        normalized_val = float(val)
        try:
            normalized_val = int(val)
        except ValueError:
            pass
        return normalized_val

    def parse_iterable(self):
        """Recursively parse an iterable object

        This will return a local representation of the parsed data, except for
        NAME nodes. This does not currently attempt to perform lookup on the
        object names defined in an iterable.

        This is mostly a naive implementation and won't handle complex
        structures. This is only currently meant to parse simple iterables, such
        as ``__all__`` and class parent classes on class definition.
        """
        content = None
        is_list = True
        while self.current is not None:
            if self.current.kind == tk.STRING:
                content.append(self.parse_string())
            elif self.current.kind == tk.NUMBER:
                content.append(self.parse_number())
            elif self.current.kind == tk.NAME:
                # Handle generators
                if self.current.value == 'for' and not content:
                    is_list = False
                # TODO this is dropped for now, but will can be handled with an
                # object lookup in the future, if we decide to track assignment.
                # content.append(self.parse_object_identifier())
                self.stream.move()
            elif self.current.kind == tk.OP and self.current.value in '[(':
                if content is None:
                    content = []
                    self.stream.move()
                else:
                    content.append(self.parse_iterable())
                continue
            elif self.current.kind == tk.OP and self.current.value in '])':
                self.stream.move()
                if is_list:
                    return content
                # Discard generator because we can't do anything with them
                return []
            else:
                self.stream.move()

    def parse_docstring(self):
        """Clean up object docstring"""
        docstring = super(ParserExtra, self).parse_docstring()
        if not docstring:
            docstring = ''
        docstring = textwrap.dedent(docstring)
        docstring = docstring.replace("'''", '').replace('"""', '')
        return docstring

    def parse_all(self):
        """Parse __all__ assignment

        This differs from the default __all__ assignment processing by:

         * Accepting multiple __all__ assignments
         * Doesn't throw exceptions on edge cases
         * Parses NAME nodes (but throws them out for now
        """
        assert self.current.value == '__all__'
        self.consume(tk.NAME)
        if self.current.kind != tk.OP or self.current.value not in ['=', '+=']:
            return
        assign_op = self.current.value
        self.consume(tk.OP)

        if self.all is None:
            self.all = []

        all_content = []
        # Support [], [] + [], and [] + foo.__all__ by iterating of list
        # assignments
        while True:
            if self.current.kind == tk.OP and self.current.value in '([':
                content = self.parse_iterable()
                all_content.extend(content)
            elif self.current.kind == tk.NAME:
                name = self.parse_object_identifier()
                # TODO Skip these for now. In the future, this name should be
                # converted to an object that will be resolved after we've
                # parsed at a later stage in the mapping process.
                # all_content.append(name)
            if self.current.kind == tk.OP and self.current.value == '+':
                self.stream.move()
            else:
                break

        if assign_op == '=':
            self.all = all_content
        elif assign_op == '+=':
            self.all += all_content
