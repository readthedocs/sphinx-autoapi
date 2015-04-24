import os
import yaml
import fnmatch

from sphinx.util.console import darkgreen

from .settings import env


class AutoAPIBase(object):

    language = 'base'
    type = 'base'

    def __init__(self, obj):
        self.obj = obj

    def render(self, ctx=None):
        if not ctx:
            ctx = {}
        template = env.get_template(
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


class UnknownType(AutoAPIBase):

    def render(self, ctx=None):
        print "Unknown Type: %s" % (self.obj['type'])
        super(UnknownType, self).render(ctx=ctx)


class AutoAPIDomain(object):

    '''Base class for domain handling

    :param app: Sphinx application instance
    '''

    namespaces = {}
    objects = {}
    top_level_objects = {}

    def __init__(self, app):
        self.app = app

    def read_file(self, path):
        '''Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        '''
        # TODO support JSON here
        # TODO sphinx way of reporting errors in logs?
        try:
            with open(path, 'r') as handle:
                obj = yaml.safe_load(handle)
        except IOError:
            raise Warning('Error reading file: {0}'.format(path))
        except yaml.YAMLError:
            raise Warning('Error parsing file: {0}'.format(path))
        return obj

    def create_class(self, obj):
        '''Create class object from obj'''
        raise NotImplementedError

    def get_config(self, key):
        if self.app.config is not None:
            return getattr(self.app.config, key, None)

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
