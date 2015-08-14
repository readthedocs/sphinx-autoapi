from collections import defaultdict
import os
import subprocess
import traceback
import shutil

import yaml
from sphinx.util.osutil import ensuredir
from sphinx.util.console import darkgreen, bold
from sphinx.errors import ExtensionError

from .base import PythonMapperBase, SphinxMapperBase


class DotNetSphinxMapper(SphinxMapperBase):

    '''Auto API domain handler for .NET

    Searches for YAML files, and soon to be JSON files as well, for auto API
    sources

    :param app: Sphinx application passed in as part of the extension
    '''

    top_namespaces = {}

    def load(self, patterns, dir, ignore=None, **kwargs):
        '''
        Load objects from the filesystem into the ``paths`` dictionary.

        '''
        raise_error = kwargs.get('raise_error', True)
        all_files = set()
        for _file in self.find_files(patterns=patterns, dir=dir, ignore=ignore):
            # Iterating for Sphinx output clarify
            all_files.add(_file)
        if all_files:
            try:
                command = ['docfx', 'metadata', '--raw', '--force']
                command.extend(all_files)
                proc = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    env=dict((key, os.environ[key])
                             for key in ['PATH', 'DNX_PATH', 'HOME']
                             if key in os.environ),
                )
                _, error_output = proc.communicate()
                if error_output:
                    self.app.warn(error_output)
            except (OSError, subprocess.CalledProcessError) as e:
                self.app.warn('Error generating metadata: {0}'.format(e))
                if raise_error:
                    raise ExtensionError('Failure in docfx while generating AutoAPI output.')
        # We now have yaml files
        for xdoc_path in self.find_files(patterns=['*.yml'], dir='_api_', ignore=ignore):
            data = self.read_file(path=xdoc_path)
            if data:
                self.paths[xdoc_path] = data

    def read_file(self, path, **kwargs):
        '''Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        '''
        try:
            with open(path, 'r') as handle:
                parsed_data = yaml.safe_load(handle)
                return parsed_data
        except IOError:
            self.app.warn('Error reading file: {0}'.format(path))
        except TypeError:
            self.app.warn('Error reading file: {0}'.format(path))
        return None

    # Subclassed to iterate over items
    def map(self, options=None, **kwargs):
        '''Trigger find of serialized sources and build objects'''
        for path, data in self.paths.items():
            for item in data['items']:
                for obj in self.create_class(item, options):
                    self.add_object(obj)

        self.organize_objects()

    def create_class(self, data, options=None, **kwargs):
        '''
        Return instance of class based on Roslyn type property

        Data keys handled here:

            type
                Set the object class

            items
                Recurse into :py:meth:`create_class` to create child object
                instances

        :param data: dictionary data from Roslyn output artifact
        '''

        obj_map = dict(
            (cls.type, cls) for cls
            in ALL_CLASSES
        )
        try:
            cls = obj_map[data['type'].lower()]
        except KeyError:
            self.app.warn('Unknown type: %s' % data)
        else:
            obj = cls(data, jinja_env=self.jinja_env, options=options)

            # Append child objects
            # TODO this should recurse in the case we're getting back more
            # complex argument listings

            yield obj

    def add_object(self, obj):
        '''Add object to local and app environment storage

        :param obj: Instance of a .NET object
        '''
        if obj.top_level_object:
            if isinstance(obj, DotNetNamespace):
                self.namespaces[obj.name] = obj
        self.objects[obj.id] = obj

    def organize_objects(self):
        '''Organize objects and namespaces'''

        def _render_children(obj):
            for child in obj.children_strings:
                child_object = self.objects.get(child)
                if child_object:
                    obj.item_map[child_object.plural].append(child_object)
                    obj.children.append(child_object)

            for key in obj.item_map:
                obj.item_map[key].sort()

        def _recurse_ns(obj):
            if not obj:
                return
            namespace = obj.top_namespace
            if namespace is not None:
                ns_obj = self.top_namespaces.get(namespace)
                if ns_obj is None or not isinstance(ns_obj, DotNetNamespace):
                    for ns_obj in self.create_class({'uid': namespace,
                                                     'type': 'namespace'}):
                        self.top_namespaces[ns_obj.id] = ns_obj
                if obj not in ns_obj.children and namespace != obj.id:
                    ns_obj.children.append(obj)

        for obj in self.objects.values():
            _render_children(obj)
            _recurse_ns(obj)

        # Clean out dead namespaces
        for key, ns in self.top_namespaces.copy().items():
            if len(ns.children) == 0:
                del self.top_namespaces[key]

        for key, ns in self.namespaces.items():
            if len(ns.children) == 0:
                del self.namespaces[key]

    def output_rst(self, root, source_suffix):
        for id, obj in self.objects.items():

            if not obj or not obj.top_level_object:
                continue

            rst = obj.render()
            if not rst:
                continue

            try:
                filename = obj.name.split('(')[0]
            except IndexError:
                filename = id
            filename = filename.replace('#', '-')
            detail_dir = os.path.join(root, *filename.split('.'))
            ensuredir(detail_dir)
            path = os.path.join(detail_dir, '%s%s' % ('index', source_suffix))
            with open(path, 'wb+') as detail_file:
                detail_file.write(rst.encode('utf-8'))

        # Render Top Index
        top_level_index = os.path.join(root, 'index.rst')
        with open(top_level_index, 'wb+') as top_level_file:
            content = self.jinja_env.get_template('index.rst')
            top_level_file.write(content.render(pages=self.namespaces.values()).encode('utf-8'))

    @staticmethod
    def build_finished(app, exception):
        if app.verbosity > 1:
            app.info(bold('[AutoAPI] ') + darkgreen('Cleaning generated .yml files'))
        if os.path.exists('_api_'):
            shutil.rmtree('_api_')


class DotNetPythonMapper(PythonMapperBase):

    '''Base .NET object representation'''

    language = 'dotnet'

    def __init__(self, obj, **kwargs):
        super(DotNetPythonMapper, self).__init__(obj, **kwargs)

        # Always exist
        self.id = obj.get('uid', obj.get('id'))
        self.name = obj.get('fullName', self.id)

        # Optional
        self.fullname = obj.get('fullName')
        self.summary = obj.get('summary', '')
        self.parameters = []
        self.items = obj.get('items', [])
        self.children_strings = obj.get('children', [])
        self.children = []
        self.item_map = defaultdict(list)
        self.inheritance = []

        # Syntax example and parameter list
        syntax = obj.get('syntax', None)
        self.example = ''
        if syntax is not None:
            # Code example
            try:
                self.example = syntax['content']
            except (KeyError, TypeError):
                traceback.print_exc()

            self.parameters = []
            for param in syntax.get('parameters', []):
                if 'id' in param:
                    self.parameters.append({
                        'name': param.get('id'),
                        'type': param.get('type'),
                        'desc': param.get('description', '')
                    })

            self.returns = syntax.get('return', None)

        # Inheritance
        # TODO Support more than just a class type here, should support enum/etc
        self.inheritance = [DotNetClass({'uid': name, 'name': name})
                            for name in obj.get('inheritance', [])]

    def __str__(self):
        return '<{cls} {id}>'.format(cls=self.__class__.__name__,
                                     id=self.id)

    @property
    def short_name(self):
        '''Shorten name property'''
        return self.name.split('.')[-1]

    @property
    def edit_link(self):
        try:
            repo = self.source['remote']['repo'].replace('.git', '')
            path = self.path
            return '{repo}/blob/master/{path}'.format(
                repo=repo,
                path=path,
            )
        except:
            return ''

    @property
    def source(self):
        return self.obj.get('source')

    @property
    def path(self):
        return self.source['path']

    @property
    def namespace(self):
        pieces = self.id.split('.')[:-1]
        if pieces:
            return '.'.join(pieces)

    @property
    def top_namespace(self):
        pieces = self.id.split('.')[:2]
        if pieces:
            return '.'.join(pieces)

    @property
    def ref_type(self):
        return self.type

    @property
    def ref_directive(self):
        return self.type

    @property
    def ref_name(self):
        '''Return object name suitable for use in references

        Escapes several known strings that cause problems, including the
        following reference syntax::

            :dotnet:cls:`Foo.Bar<T>`

        As the `<T>` notation is also special syntax in references, indicating
        the reference to Foo.Bar should be named T.

        See: http://sphinx-doc.org/domains.html#role-cpp:any
        '''
        return (self.name
                .replace('<', '\<')
                .replace('`', '\`'))

    @property
    def ref_short_name(self):
        '''Same as above, return the truncated name instead'''
        return self.ref_name.split('.')[-1]


class DotNetNamespace(DotNetPythonMapper):
    type = 'namespace'
    ref_directive = 'ns'
    plural = 'namespaces'
    top_level_object = True


class DotNetMethod(DotNetPythonMapper):
    type = 'method'
    ref_directive = 'meth'
    plural = 'methods'


class DotNetProperty(DotNetPythonMapper):
    type = 'property'
    ref_directive = 'prop'
    plural = 'properties'


class DotNetEnum(DotNetPythonMapper):
    type = 'enum'
    ref_type = 'enumeration'
    ref_directive = 'enum'
    plural = 'enumerations'
    top_level_object = True


class DotNetStruct(DotNetPythonMapper):
    type = 'struct'
    ref_type = 'structure'
    ref_directive = 'struct'
    plural = 'structures'
    top_level_object = True


class DotNetConstructor(DotNetPythonMapper):
    type = 'constructor'
    ref_directive = 'ctor'
    plural = 'constructors'


class DotNetInterface(DotNetPythonMapper):
    type = 'interface'
    ref_directive = 'iface'
    plural = 'interfaces'
    top_level_object = True


class DotNetDelegate(DotNetPythonMapper):
    type = 'delegate'
    ref_directive = 'del'
    plural = 'delegates'
    top_level_object = True


class DotNetClass(DotNetPythonMapper):
    type = 'class'
    ref_directive = 'cls'
    plural = 'classes'
    top_level_object = True


class DotNetField(DotNetPythonMapper):
    type = 'field'
    plural = 'fields'


class DotNetEvent(DotNetPythonMapper):
    type = 'event'
    plural = 'events'

ALL_CLASSES = [
    DotNetNamespace, DotNetClass, DotNetEnum, DotNetStruct,
    DotNetInterface, DotNetDelegate, DotNetProperty, DotNetMethod,
    DotNetConstructor, DotNetField, DotNetEvent
]
