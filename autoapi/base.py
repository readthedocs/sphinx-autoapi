import yaml

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
        context = {}
        # TODO deprecate this, it doesn't handle things like class variables
        context.update(self.__dict__)
        context['object'] = self
        return context


class UnknownType(AutoAPIBase):

    def render(self, ctx=None):
        print "Unknown Type: %s" % (self.obj['type'])
        super(UnknownType, self).render(ctx=ctx)


class AutoAPIDomain(object):
    '''Base class for domain handling

    :param app: Sphinx application instance
    '''

    namespaces = {}
    objects = []

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
