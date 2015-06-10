import os
import fnmatch

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from sphinx.util.console import darkgreen
from sphinx.util.osutil import ensuredir


from ..settings import TEMPLATE_DIR


class PythonMapperBase(object):

    language = 'base'
    type = 'base'

    def __init__(self, obj, jinja_env=None):
        self.obj = obj
        if jinja_env:
            self.jinja_env = jinja_env

    def render(self, ctx=None):
        if not ctx:
            ctx = {}
        try:
            template = self.jinja_env.get_template(
                '{language}/{type}.rst'.format(language=self.language, type=self.type)
            )
        except TemplateNotFound:
            # Use a try/except here so we fallback to language specific defaults, over base defaults
            template = self.jinja_env.get_template(
                'base/{type}.rst'.format(language=self.language, type=self.type)
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
        if isinstance(other, PythonMapperBase):
            return self.id < other.id
        return super(PythonMapperBase, self).__lt__(other)

    def __str__(self):
        return '<{cls} {id}>'.format(cls=self.__class__.__name__,
                                     id=self.id)

    @property
    def short_name(self):
        '''Shorten name property'''
        return self.name.split('.')[-1]

    @property
    def ref_type(self):
        return self.type

    @property
    def ref_directive(self):
        return self.type

    @property
    def namespace(self):
        pieces = self.id.split('.')[:-1]
        if pieces:
            return '.'.join(pieces)


class SphinxMapperBase(object):

    '''Base class for mapping `PythonMapperBase` objects to Sphinx.

    :param app: Sphinx application instance
    '''

    # Mapping of {filepath -> raw data}
    paths = {}
    # Mapping of {object id -> Python Object}
    objects = {}

    namespaces = {}
    top_level_objects = {}

    def __init__(self, app):
        self.app = app

        TEMPLATE_PATHS = [TEMPLATE_DIR]
        USER_TEMPLATE_DIR = self.get_config('autoapi_template_dir')
        if USER_TEMPLATE_DIR:
            # Put at the front so it's loaded first
            TEMPLATE_PATHS.insert(0, USER_TEMPLATE_DIR)

        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATE_PATHS)
        )

    def load(self, pattern, dir, ignore=[]):
        '''
        Load objects from the filesystem into the ``paths`` dictionary.

        '''
        for path in self.find_files(pattern=pattern, dir=dir, ignore=ignore):
            data = self.read_file(path=path)
            if data:
                self.paths[path] = data

    def find_files(self, pattern, dir, ignore):
        files_to_read = []
        for root, dirnames, filenames in os.walk(dir):
            for filename in fnmatch.filter(filenames, pattern):

                # Skip ignored files
                for ignore_pattern in ignore:
                    if fnmatch.fnmatch(filename, ignore_pattern):
                        print "Ignoring %s/%s" % (root, filename)
                        continue

                # Make sure the path is full
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

    def read_file(self, path, **kwargs):
        '''Read file input into memory

        :param path: Path of file to read
        '''
        # TODO support JSON here
        # TODO sphinx way of reporting errors in logs?
        raise NotImplementedError

    def add_object(self, obj):
        '''
        Add object to local and app environment storage

        :param obj: Instance of a AutoAPI object
        '''
        self.objects[obj.id] = obj

    def get_config(self, key, default=None):
        if self.app.config is not None:
            return getattr(self.app.config, key, default)

    def map(self):
        '''Trigger find of serialized sources and build objects'''
        for path, data in self.paths.items():
            for obj in self.create_class(data):
                self.add_object(obj)

    def create_class(self, obj):
        '''
        Create class object.

        :param obj: Instance of a AutoAPI object
        '''
        raise NotImplementedError

    def output_rst(self, root, source_suffix):
        for id, obj in self.objects.items():

            if not obj:
                continue

            rst = obj.render()
            if not rst:
                continue

            try:
                filename = id.split('(')[0]
            except IndexError:
                filename = id
            filename = filename.replace('#', '-')
            detail_dir = os.path.join(root, *filename.split('.'))
            ensuredir(detail_dir)
            path = os.path.join(detail_dir, '%s%s' % ('index', source_suffix))
            with open(path, 'w+') as detail_file:
                detail_file.write(rst.encode('utf-8'))

        # Render Top Index
        top_level_index = os.path.join(root, 'index.rst')
        with open(top_level_index, 'w+') as top_level_file:
            content = self.jinja_env.get_template('index.rst')
            top_level_file.write(content.render())
