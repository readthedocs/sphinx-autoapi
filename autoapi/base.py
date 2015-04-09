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
        ctx.update(**self.__dict__)
        return template.render(**ctx)

    def get_absolute_path(self):
        return "/autoapi/{type}/{name}".format(
            type=self.type,
            name=self.name,
        )


class UnknownType(AutoAPIBase):

    def render(self, ctx=None):
        print "Unknown Type: %s" % (self.obj['type'])
        super(UnknownType, self).render(ctx=ctx)
