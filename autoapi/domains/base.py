import os
import yaml
import json
import fnmatch

from jinja2 import Environment, FileSystemLoader
from sphinx.util.console import darkgreen


from ..settings import TEMPLATE_DIR


class AutoAPIBase(object):

    language = 'base'
    type = 'base'

    def __init__(self, obj):
        self.obj = obj

        TEMPLATE_PATHS = [TEMPLATE_DIR]
        USER_TEMPLATE_DIR = self.get_config('autoapi_template_dir')
        if USER_TEMPLATE_DIR:
            # Put at the front so it's loaded first
            TEMPLATE_PATHS.insert(0, USER_TEMPLATE_DIR)

        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATE_PATHS)
        )

    def render(self, ctx=None):
        if not ctx:
            ctx = {}
        template = self.jinja_env.get_template(
            '{language}/{type}.rst'.format(language=self.language, type=self.type)
        )
        ctx.update(**self.get_context_data())
        return template.render(**ctx)

    def get_absolute_path(self):
        return "/autoapi/{type}/{name}".format(
            type=self.type,
            name=self.name,
        )

    def get_context_data(self):
        return {
            'obj': self
        }

    def __lt__(self, other):
        '''Object sorting comparison'''
        if isinstance(other, AutoAPIBase):
            return self.id < other.id
        return super(AutoAPIBase, self).__lt__(other)

    def __str__(self):
        return '<{cls} {id}>'.format(cls=self.__class__.__name__,
                                     id=self.id)


class AutoAPIDomain(object):

    '''Base class for domain handling

    :param app: Sphinx application instance
    '''

    namespaces = {}
    objects = {}
    top_level_objects = {}

    def __init__(self, app):
        self.app = app

    def read_file(self, path, format='yaml'):
        '''Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        '''
        # TODO support JSON here
        # TODO sphinx way of reporting errors in logs?
        try:
            with open(path, 'r') as handle:
                if format == 'yaml':
                    obj = yaml.safe_load(handle)
                elif format == 'json':
                    obj = json.load(handle)
        except IOError:
            raise Warning('Error reading file: {0}'.format(path))
        except yaml.YAMLError:
            raise Warning('Error parsing file: {0}'.format(path))
        except ValueError:
            raise Warning('Error parsing file: {0} at {1}'.format(path, json.last_error_position))
        return obj

    def add_object(self, obj):
        '''
        Add object to local and app environment storage

        :param obj: Instance of a AutoAPI object
        '''
        self.app.env.autoapi_data.append(obj)
        self.objects[obj.name] = obj

    def get_config(self, key, default=None):
        if self.app.config is not None:
            return getattr(self.app.config, key, default)

    def find_files(self, pattern='*.yaml'):
        '''Find YAML/JSON files to parse for namespace information'''
        # TODO do an intelligent glob here, we're picking up too much
        files_to_read = []
        absolute_dir = os.path.normpath(self.get_config('autoapi_dir'))
        for root, dirnames, filenames in os.walk(absolute_dir):
            for filename in fnmatch.filter(filenames, pattern):

                # Skip ignored files
                for ignore_pattern in self.get_config('autoapi_ignore'):
                    if fnmatch.fnmatch(filename, ignore_pattern):
                        print "Ignoring %s/%s" % (root, filename)
                        continue

                if os.path.isabs(filename):
                    files_to_read.append(os.path.join(filename))
                else:
                    files_to_read.append(os.path.join(root, filename))

        for _path in self.app.status_iterator(
                files_to_read,
                '[AutoAPI] Reading files... ',
                darkgreen,
                len(files_to_read)):
            yield _path

    def get_objects(self, pattern, format='yaml'):
        '''Trigger find of serialized sources and build objects'''
        for path in self.find_files(pattern):
            data = self.read_file(path, format=format)
            if data:
                for obj in self.create_class(data):
                    self.add_object(obj)

    def create_class(self, obj):
        '''
        Create class object.

        :param obj: Instance of a AutoAPI object
        '''
        raise NotImplementedError

    def write_indexes(self):
        # Write Index
        top_level_index = os.path.join(self.get_config('autoapi_root'),
                                       'index.rst')
        with open(top_level_index, 'w+') as top_level_file:
            content = self.jinja_env.get_template('index.rst')
            top_level_file.write(content.render())
