from .settings import env


class AutoAPIBase(object):

    language = 'base'
    type = 'base'
    header = '-'

    def __init__(self, obj):
        self.obj = obj

    def render(self, ctx=None):
        if not ctx:
            ctx = {}
        template = env.get_template(
            '{language}/{type}.rst'.format(language=self.language, type=self.type)
        )
        ctx.update(**self.obj)
        return template.render(ctx)


class UnknownType(AutoAPIBase):

    def render(self, ctx=None):
        print "Unknown Type: %s" % (self.obj['type'])
        super(UnknownType, self).render(ctx=ctx)
