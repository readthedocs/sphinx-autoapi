import sys
import os
import collections

import astroid
import sphinx
import sphinx.util.docstrings

from .base import PythonMapperBase, SphinxMapperBase
from . import astroid_utils
from ..utils import slugify


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
            dir_root = dir_
            if os.path.exists(os.path.join(dir_, '__init__.py')):
                dir_root = os.path.abspath(os.path.join(dir_, os.pardir))

            for path in self.find_files(patterns=patterns, dirs=[dir_], ignore=ignore):
                data = self.read_file(path=path)
                if data:
                    data['relative_path'] = os.path.relpath(path, dir_root)
                    self.paths[path] = data

    def read_file(self, path, **kwargs):
        """Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        """
        try:
            parsed_data = Parser().parse_file(path)
            return parsed_data
        except (IOError, TypeError, ImportError):
            self.app.warn('Error reading file: {0}'.format(path))
        return None

    def map(self, options=None):
        super(PythonSphinxMapper, self).map(options)

        parents = {obj.name: obj for obj in self.objects.values()}
        for obj in self.objects.values():
            parent_name = obj.name.rsplit('.', 1)[0]
            if parent_name in parents and parent_name != obj.name:
                parent = parents[parent_name]
                attr = 'sub{}s'.format(obj.type)
                getattr(parent, attr).append(obj)

        for obj in self.objects.values():
            obj.submodules.sort()
            obj.subpackages.sort()

    def create_class(self, data, options=None, **kwargs):
        """Create a class from the passed in data

        :param data: dictionary data of parser output
        """
        obj_map = dict((cls.type, cls) for cls
                       in [PythonClass, PythonFunction, PythonModule,
                           PythonMethod, PythonPackage, PythonAttribute,
                           PythonData, PythonException])
        try:
            cls = obj_map[data['type']]
        except KeyError:
            self.app.warn("Unknown type: %s" % data['type'])
        else:
            obj = cls(
                data,
                jinja_env=self.jinja_env,
                options=self.app.config.autoapi_options,
                class_content=self.app.config.autoapi_python_class_content,
                **kwargs
            )

            lines = sphinx.util.docstrings.prepare_docstring(obj.docstring)
            try:
                if lines:
                    self.app.emit(
                        'autodoc-process-docstring',
                        cls.type,
                        obj.name,
                        None,  # object
                        None,  # options
                        lines,
                    )
            except KeyError:
                if (sphinx.version_info >= (1, 6)
                        and 'autodoc-process-docstring' in self.app.events.events):
                    raise
            else:
                obj.docstring = '\n'.join(lines)

            for child_data in data.get('children', []):
                for child_obj in self.create_class(child_data, options=options,
                                                   **kwargs):
                    obj.children.append(child_obj)
            yield obj

    def _output_top_rst(self, root):
        # Render Top Index
        top_level_index = os.path.join(root, 'index.rst')
        pages = [obj for obj in self.objects.values() if '.' not in obj.name]
        with open(top_level_index, 'w+') as top_level_file:
            content = self.jinja_env.get_template('index.rst')
            top_level_file.write(content.render(pages=pages))


class PythonPythonMapper(PythonMapperBase):

    language = 'python'
    is_callable = False

    def __init__(self, obj, class_content='class', **kwargs):
        super(PythonPythonMapper, self).__init__(obj, **kwargs)

        self.name = obj['name']
        self.id = slugify(self.name)

        # Optional
        self.children = []
        self.args = obj.get('args')
        self.docstring = obj['doc']

        # For later
        self.item_map = collections.defaultdict(list)
        self._class_content = class_content

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        self._args = value

    @property
    def docstring(self):
        return self._docstring

    @docstring.setter
    def docstring(self, value):
        self._docstring = value

    @property
    def is_undoc_member(self):
        return not bool(self.docstring)

    @property
    def is_private_member(self):
        return (
            self.short_name.startswith('_')
            and not self.short_name.endswith('__')
        )

    @property
    def is_special_member(self):
        return (
            self.short_name.startswith('__')
            and self.short_name.endswith('__')
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

    @property
    def summary(self):
        for line in self.docstring.splitlines():
            line = line.strip()
            if line:
                return line

        return ''

    def _children_of_type(self, type_):
        return list(child for child in self.children if child.type == type_)


class PythonFunction(PythonPythonMapper):
    type = 'function'
    is_callable = True
    ref_directive = 'func'


class PythonMethod(PythonPythonMapper):
    type = 'method'
    is_callable = True
    ref_directive = 'meth'

    def __init__(self, obj, **kwargs):
        super(PythonMethod, self).__init__(obj, **kwargs)

        self.method_type = obj['method_type']

    @property
    def display(self):
        if self.short_name == '__init__':
            return False

        return super(PythonMethod, self).display


class PythonData(PythonPythonMapper):
    """Global, module level data."""
    type = 'data'

    def __init__(self, obj, **kwargs):
        super(PythonData, self).__init__(obj, **kwargs)

        self.value = obj.get('value')


class PythonAttribute(PythonData):
    """An object/class level attribute."""
    type = 'attribute'


class TopLevelPythonPythonMapper(PythonPythonMapper):
    top_level_object = True
    ref_directive = 'mod'

    def __init__(self, obj, **kwargs):
        super(TopLevelPythonPythonMapper, self).__init__(obj, **kwargs)

        self._resolve_name()

        self.subpackages = []
        self.submodules = []

    @property
    def functions(self):
        return self._children_of_type('function')

    @property
    def classes(self):
        return self._children_of_type('class')


class PythonModule(TopLevelPythonPythonMapper):
    type = 'module'

    def _resolve_name(self):
        name = self.obj['relative_path']
        name = name.replace(os.sep, '.')
        ext = '.py'
        if name.endswith(ext):
            name = name[:-len(ext)]

        self.name = name


class PythonPackage(TopLevelPythonPythonMapper):
    type = 'package'

    def _resolve_name(self):
        name = self.obj['relative_path']

        exts = [os.sep + '__init__.py', '.py']
        for ext in exts:
            if name.endswith(ext):
                name = name[:-len(ext)]
                name = name.replace(os.sep, '.')

        self.name = name


class PythonClass(PythonPythonMapper):
    type = 'class'

    def __init__(self, obj, **kwargs):
        super(PythonClass, self).__init__(obj, **kwargs)

        self.bases = obj['bases']

    @PythonPythonMapper.args.getter
    def args(self):
        args = self._args

        constructor = self.constructor
        if constructor:
            args = constructor.args

        if args.startswith('self'):
            args = args[4:].lstrip(',').lstrip()

        return args

    @PythonPythonMapper.docstring.getter
    def docstring(self):
        docstring = super(PythonClass, self).docstring

        if self._class_content in ('both', 'init'):
            constructor_docstring = self.constructor_docstring
            if constructor_docstring:
                if self._class_content == 'both':
                    docstring = '{0}\n{1}'.format(
                        docstring, constructor_docstring,
                    )
                else:
                    docstring = constructor_docstring

        return docstring

    @property
    def methods(self):
        return self._children_of_type('method')

    @property
    def attributes(self):
        return self._children_of_type('attribute')

    @property
    def constructor(self):
        for child in self.children:
            if child.short_name == '__init__':
                return child

        return None

    @property
    def constructor_docstring(self):
        docstring = ''

        constructor = self.constructor
        if constructor and constructor.docstring:
            docstring = constructor.docstring
        else:
            for child in self.children:
                if child.short_name == '__new__':
                    docstring = child.docstring
                    break

        return docstring


class PythonException(PythonClass):
    type = 'exception'


class Parser(object):
    def parse_file(self, file_path):
        directory, filename = os.path.split(file_path)
        module_part = os.path.splitext(filename)[0]
        module_parts = collections.deque([module_part])
        while os.path.isfile(os.path.join(directory, '__init__.py')):
            directory, module_part = os.path.split(directory)
            if module_part:
                module_parts.appendleft(module_part)

        module_name = '.'.join(module_parts)
        node = astroid.MANAGER.ast_from_file(file_path, module_name)
        return self.parse(node)

    def parse_assign(self, node):
        doc = ''
        doc_node = node.next_sibling()
        if (isinstance(doc_node, astroid.nodes.Expr)
                and isinstance(doc_node.value, astroid.nodes.Const)):
            doc = doc_node.value.value

        type_ = 'data'
        if (isinstance(node.scope(), astroid.nodes.ClassDef)
                or astroid_utils.is_constructor(node.scope())):
            type_ = 'attribute'

        assign_value = astroid_utils.get_assign_value(node)
        if not assign_value:
            return []

        target, value = assign_value
        data = {
            'type': type_,
            'name': target,
            'doc': doc,
            'value': value,
            'from_line_no': node.fromlineno,
            'to_line_no': node.tolineno,
        }

        return [data]

    def parse_classdef(self, node, data=None):
        type_ = 'class'
        if astroid_utils.is_exception(node):
            type_ = 'exception'

        args = ''
        try:
            constructor = node.lookup('__init__')[1]
        except IndexError:
            pass
        else:
            if isinstance(constructor, astroid.nodes.FunctionDef):
                args = constructor.args.as_string()

        basenames = list(astroid_utils.get_full_basenames(node.bases, node.basenames))

        data = {
            'type': type_,
            'name': node.name,
            'args': args,
            'bases': basenames,
            'doc': node.doc or '',
            'from_line_no': node.fromlineno,
            'to_line_no': node.tolineno,
            'children': [],
        }

        for child in node.get_children():
            child_data = self.parse(child)
            if child_data:
                data['children'].extend(child_data)

        return [data]

    def _parse_property(self, node):
        data = {
            'type': 'attribute',
            'name': node.name,
            'doc': node.doc or '',
            'from_line_no': node.fromlineno,
            'to_line_no': node.tolineno,
        }

        return [data]

    def parse_functiondef(self, node):
        if astroid_utils.is_decorated_with_property(node):
            return self._parse_property(node)
        if astroid_utils.is_decorated_with_property_setter(node):
            return []

        type_ = 'function' if node.type == 'function' else 'method'

        data = {
            'type': type_,
            'name': node.name,
            'args': node.args.as_string(),
            'doc': node.doc or '',
            'from_line_no': node.fromlineno,
            'to_line_no': node.tolineno,
        }

        if type_ == 'method':
            data['method_type'] = node.type

        result = [data]

        if node.name == '__init__':
            for child in node.get_children():
                if isinstance(child, astroid.Assign):
                    child_data = self.parse_assign(child)
                    result.extend(child_data)

        return result

    def parse_module(self, node):
        path = node.path
        if isinstance(node.path, list):
            path = node.path[0] if node.path else None

        type_ = 'module'
        if path.endswith('__init__.py'):
            type_ = 'package'

        data = {
            'type': type_,
            'name': node.name,
            'doc': node.doc or '',
            'children': [],
            'file_path': path,
        }

        for child in node.get_children():
            child_data = self.parse(child)
            if child_data:
                data['children'].extend(child_data)

        return data

    def parse(self, node):
        data = {}

        node_type = node.__class__.__name__.lower()
        parse_func = getattr(self, 'parse_' + node_type, None)
        if parse_func:
            data = parse_func(node)
        else:
            for child in node.get_children():
                data = self.parse(child)
                if data:
                    break

        return data
