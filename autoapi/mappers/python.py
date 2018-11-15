import collections
import copy
import os

import astroid
import sphinx
import sphinx.util.docstrings

from .base import PythonMapperBase, SphinxMapperBase
from . import astroid_utils
from ..utils import slugify

try:
    _TEXT_TYPE = unicode
except NameError:
    _TEXT_TYPE = str


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

    def _resolve_placeholders(self):
        """Resolve objects that have been imported from elsewhere."""
        placeholders = []
        all_data = {}
        child_stack = []
        # Initialise the stack with module level objects
        for data in self.paths.values():
            all_data[data['name']] = data

            for child in data['children']:
                child_stack.append((data, data['name'], child))

        # Find all placeholders and everything that can be resolved to
        while child_stack:
            parent, parent_name, data = child_stack.pop()
            if data['type'] == 'placeholder':
                placeholders.append((parent, data))

            full_name = parent_name + '.' + data['name']
            all_data[full_name] = data

            for child in data.get('children', ()):
                child_stack.append((data, full_name, child))

        # Resolve all placeholders
        for parent, placeholder in placeholders:
            # Check if this was resolved by a previous iteration
            if placeholder['type'] != 'placeholder':
                continue

            if placeholder['original_path'] not in all_data:
                parent['children'].remove(placeholder)
                self.app.debug(
                    'Could not resolve {0} for {1}.{2}'.format(
                        placeholder['original_path'],
                        parent['name'],
                        placeholder['name'],
                    )
                )
                continue

            # Find import chains and resolve the placeholders together
            visited = {id(placeholder): placeholder}
            original = all_data[placeholder['original_path']]
            while (original['type'] == 'placeholder'
                   # Or it's an already resolved placeholder
                   or 'from_line_no' not in original):
                # This is a cycle that we cannot resolve
                if id(original) in visited:
                    assert original['type'] == 'placeholder'
                    parent['children'].remove(placeholder)
                    break
                visited[id(original)] = original
                original = all_data[original['original_path']]
            else:
                if original['type'] in ('package', 'module'):
                    parent['children'].remove(placeholder)
                    continue

                for to_resolve in visited.values():
                    new = copy.deepcopy(original)
                    new['name'] = to_resolve['name']
                    new['full_name'] = to_resolve['full_name']
                    new['original_path'] = original['full_name']
                    del new['from_line_no']
                    del new['to_line_no']
                    stack = list(new.get('children', ()))
                    while stack:
                        data = stack.pop()
                        assert data['full_name'].startswith(
                            original['full_name']
                        )
                        suffix = data['full_name'][len(original['full_name']):]
                        data['full_name'] = new['full_name'] + suffix
                        del data['from_line_no']
                        del data['to_line_no']
                        stack.extend(data.get('children', ()))
                    to_resolve.clear()
                    to_resolve.update(new)

    def map(self, options=None):
        self._resolve_placeholders()

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
                class_content=self.app.config.autoapi_python_class_content,
                options=self.app.config.autoapi_options,
                jinja_env=self.jinja_env,
                url_root=self.url_root,
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


class PythonPythonMapper(PythonMapperBase):

    language = 'python'
    is_callable = False

    def __init__(self, obj, class_content='class', **kwargs):
        super(PythonPythonMapper, self).__init__(obj, **kwargs)

        self.name = obj['name']
        self.id = obj.get('full_name', self.name)

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
    ref_directive = 'mod'

    def __init__(self, obj, **kwargs):
        super(TopLevelPythonPythonMapper, self).__init__(obj, **kwargs)

        self.top_level_object = '.' not in self.name

        self.subpackages = []
        self.submodules = []
        self.all = obj['all']

    @property
    def functions(self):
        return self._children_of_type('function')

    @property
    def classes(self):
        return self._children_of_type('class')


class PythonModule(TopLevelPythonPythonMapper):
    type = 'module'


class PythonPackage(TopLevelPythonPythonMapper):
    type = 'package'


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
    def classes(self):
        return self._children_of_type('class')

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
    def __init__(self):
        self._name_stack = []
        self._encoding = None

    def _get_full_name(self, name):
        return '.'.join(self._name_stack + [name])

    def _encode(self, to_encode):
        if self._encoding:
            try:
                return _TEXT_TYPE(to_encode, self._encoding)
            except TypeError:
                # The string was already in the correct format
                pass

        return to_encode

    def parse_file(self, file_path):
        directory, filename = os.path.split(file_path)
        module_parts = []
        if filename != '__init__.py':
            module_part = os.path.splitext(filename)[0]
            module_parts = [module_part]
        module_parts = collections.deque(module_parts)
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
            'full_name': self._get_full_name(target),
            'doc': self._encode(doc),
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
            'full_name': self._get_full_name(node.name),
            'args': args,
            'bases': basenames,
            'doc': self._encode(node.doc or ''),
            'from_line_no': node.fromlineno,
            'to_line_no': node.tolineno,
            'children': [],
        }

        self._name_stack.append(node.name)
        for child in node.get_children():
            child_data = self.parse(child)
            if child_data:
                data['children'].extend(child_data)
        self._name_stack.pop()

        return [data]

    def _parse_property(self, node):
        data = {
            'type': 'attribute',
            'name': node.name,
            'full_name': self._get_full_name(node.name),
            'doc': self._encode(node.doc or ''),
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
            'full_name': self._get_full_name(node.name),
            'args': node.args.as_string(),
            'doc': self._encode(node.doc or ''),
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
                    result.extend(data for data in child_data if data['doc'])

        return result

    def _parse_local_import_from(self, node):
        result = []

        for name, alias in node.names:
            full_name = astroid_utils.get_full_import_name(node, alias or name)

            data = {
                'type': 'placeholder',
                'name': alias or name,
                'full_name': self._get_full_name(alias or name),
                'original_path': full_name,
            }
            result.append(data)

        return result

    def parse_module(self, node):
        path = node.path
        if isinstance(node.path, list):
            path = node.path[0] if node.path else None

        type_ = 'module'
        if node.package:
            type_ = 'package'

        self._name_stack = [node.name]
        self._encoding = node.file_encoding

        data = {
            'type': type_,
            'name': node.name,
            'full_name': node.name,
            'doc': self._encode(node.doc or ''),
            'children': [],
            'file_path': path,
            'encoding': node.file_encoding,
            'all': astroid_utils.get_module_all(node),
        }

        top_name = node.name.split('.', 1)[0]
        for child in node.get_children():
            if node.package and astroid_utils.is_local_import_from(child, top_name):
                child_data = self._parse_local_import_from(child)
            else:
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
