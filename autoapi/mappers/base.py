import os
import fnmatch
from collections import OrderedDict, namedtuple
import re

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import sphinx
import sphinx.util
from sphinx.util.console import darkgreen, bold
from sphinx.util.osutil import ensuredir
import sphinx.util.logging
import unidecode

from ..settings import API_ROOT, TEMPLATE_DIR

LOGGER = sphinx.util.logging.getLogger(__name__)

Path = namedtuple("Path", ["absolute", "relative"])


class PythonMapperBase:

    """
    Base object for JSON -> Python object mapping.

    Subclasses of this object will handle their language specific JSON input,
    and map that onto this standard Python object.
    Subclasses may also include language-specific attributes on this object.

    Arguments:

    :param obj: JSON object representing this object
    :param jinja_env: A template environment for rendering this object

    Required attributes:

    :var str id: A globally unique indentifier for this object.
                 Generally a fully qualified name, including namespace.
    :var str name: A short "display friendly" name for this object.

    Optional attributes:

    :var str docstring: The documentation for this object
    :var list imports: Imports in this object
    :var list children: Children of this object
    :var list parameters: Parameters to this object
    :var list methods: Methods on this object
    """

    language = "base"
    type = "base"
    # Create a page in the output for this object.
    top_level_object = False
    _RENDER_LOG_LEVEL = "VERBOSE"

    def __init__(self, obj, jinja_env, app, options=None):
        self.app = app
        self.obj = obj
        self.options = options
        self.jinja_env = jinja_env
        self.url_root = os.path.join("/", API_ROOT)

        self.name = None
        self.id = None

    def __getstate__(self):
        """Obtains serialisable data for pickling."""
        __dict__ = self.__dict__.copy()
        __dict__.update(app=None, jinja_env=None)  # clear unpickable attributes
        return __dict__

    def render(self, **kwargs):
        LOGGER.log(self._RENDER_LOG_LEVEL, "Rendering %s", self.id)

        ctx = {}
        try:
            template = self.jinja_env.get_template(
                "{language}/{type}.rst".format(language=self.language, type=self.type)
            )
        except TemplateNotFound:
            # Use a try/except here so we fallback to language specific defaults, over base defaults
            template = self.jinja_env.get_template(
                "base/{type}.rst".format(type=self.type)
            )

        ctx.update(**self.get_context_data())
        ctx.update(**kwargs)
        return template.render(**ctx)

    @property
    def rendered(self):
        """Shortcut to render an object in templates."""
        return self.render()

    def get_context_data(self):
        return {
            "autoapi_options": self.app.config.autoapi_options,
            "include_summaries": self.app.config.autoapi_include_summaries,
            "obj": self,
            "sphinx_version": sphinx.version_info,
        }

    def __lt__(self, other):
        """Object sorting comparison"""
        if isinstance(other, PythonMapperBase):
            return self.id < other.id
        return super(PythonMapperBase, self).__lt__(other)

    def __str__(self):
        return "<{cls} {id}>".format(cls=self.__class__.__name__, id=self.id)

    @property
    def short_name(self):
        """Shorten name property"""
        return self.name.split(".")[-1]

    @property
    def pathname(self):
        """Sluggified path for filenames

        Slugs to a filename using the follow steps

        * Decode unicode to approximate ascii
        * Remove existing hypens
        * Substitute hyphens for non-word characters
        * Break up the string as paths
        """
        slug = self.name
        slug = unidecode.unidecode(slug)
        slug = slug.replace("-", "")
        slug = re.sub(r"[^\w\.]+", "-", slug).strip("-")
        return os.path.join(*slug.split("."))

    def include_dir(self, root):
        """Return directory of file"""
        parts = [root]
        parts.extend(self.pathname.split(os.path.sep))
        return "/".join(parts)

    @property
    def include_path(self):
        """Return 'absolute' path without regarding OS path separator

        This is used in ``toctree`` directives, as Sphinx always expects Unix
        path separators
        """
        parts = [self.include_dir(root=self.url_root)]
        parts.append("index")
        return "/".join(parts)

    @property
    def display(self):
        """Whether to display this object or not.

        :type: bool
        """
        return True

    @property
    def ref_type(self):
        return self.type

    @property
    def ref_directive(self):
        return self.type


class SphinxMapperBase:

    """Base class for mapping `PythonMapperBase` objects to Sphinx.

    :param app: Sphinx application instance

    """

    def __init__(self, app, template_dir=None, url_root=None):
        self.app = app

        template_paths = [TEMPLATE_DIR]

        if template_dir:
            # Put at the front so it's loaded first
            template_paths.insert(0, template_dir)

        self.jinja_env = Environment(
            loader=FileSystemLoader(template_paths),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        def _wrapped_prepare(value):
            return value

        self.jinja_env.filters["prepare_docstring"] = _wrapped_prepare
        if self.app.config.autoapi_prepare_jinja_env:
            self.app.config.autoapi_prepare_jinja_env(self.jinja_env)

        self.url_root = url_root

        # Mapping of {filepath -> raw data}
        self.paths = OrderedDict()
        # Mapping of {object id -> Python Object}
        self.objects = OrderedDict()
        # Mapping of {object id -> Python Object}
        self.all_objects = OrderedDict()
        # Mapping of {namespace id -> Python Object}
        self.namespaces = OrderedDict()
        # Mapping of {namespace id -> Python Object}
        self.top_level_objects = OrderedDict()

    def load(self, patterns, dirs, ignore=None):
        """
        Load objects from the filesystem into the ``paths`` dictionary.

        """
        paths = list(self.find_files(patterns=patterns, dirs=dirs, ignore=ignore))
        for path in sphinx.util.status_iterator(
            paths, bold("[AutoAPI] Reading files... "), "darkgreen", len(paths)
        ):
            data = self.read_file(path=path)
            if data:
                self.paths[path] = data

        return True

    @staticmethod
    def find_files(patterns, dirs, ignore):
        # pylint: disable=too-many-nested-blocks
        if not ignore:
            ignore = []

        pattern_regexes = []
        for pattern in patterns:
            regex = re.compile(fnmatch.translate(pattern).replace(".*", "(.*)"))
            pattern_regexes.append((pattern, regex))

        for _dir in dirs:
            for root, _, filenames in os.walk(_dir):
                seen = set()
                for pattern, pattern_re in pattern_regexes:
                    for filename in fnmatch.filter(filenames, pattern):
                        skip = False

                        match = re.match(pattern_re, filename)
                        norm_name = match.groups()
                        if norm_name in seen:
                            continue

                        # Skip ignored files
                        for ignore_pattern in ignore:
                            if fnmatch.fnmatch(
                                os.path.join(root, filename), ignore_pattern
                            ):
                                LOGGER.info(
                                    bold("[AutoAPI] ")
                                    + darkgreen("Ignoring %s/%s" % (root, filename))
                                )
                                skip = True

                        if skip:
                            continue

                        # Make sure the path is full
                        if not os.path.isabs(filename):
                            filename = os.path.join(root, filename)

                        yield filename
                        seen.add(norm_name)

    def read_file(self, path, **kwargs):
        """Read file input into memory

        :param path: Path of file to read
        """
        # TODO support JSON here
        # TODO sphinx way of reporting errors in logs?
        raise NotImplementedError

    def add_object(self, obj):
        """
        Add object to local and app environment storage

        :param obj: Instance of a AutoAPI object
        """
        self.objects[obj.id] = obj
        self.all_objects[obj.id] = obj
        child_stack = list(obj.children)
        while child_stack:
            child = child_stack.pop()
            self.all_objects[child.id] = child
            child_stack.extend(getattr(child, "children", ()))

    def map(self, options=None):
        """Trigger find of serialized sources and build objects"""
        for _, data in sphinx.util.status_iterator(
            self.paths.items(),
            bold("[AutoAPI] ") + "Mapping Data... ",
            length=len(self.paths),
            stringify_func=(lambda x: x[0]),
        ):
            for obj in self.create_class(data, options=options):
                self.add_object(obj)

    def create_class(self, data, options=None, **kwargs):
        """
        Create class object.

        :param data: Instance of a AutoAPI object
        """
        raise NotImplementedError

    def output_rst(self, root, source_suffix):
        for _, obj in sphinx.util.status_iterator(
            self.objects.items(),
            bold("[AutoAPI] ") + "Rendering Data... ",
            length=len(self.objects),
            verbosity="INFO",
            stringify_func=(lambda x: x[0]),
        ):
            rst = obj.render()
            if not rst:
                continue

            detail_dir = obj.include_dir(root=root)
            ensuredir(detail_dir)
            path = os.path.join(detail_dir, "%s%s" % ("index", source_suffix))
            with open(path, "wb+") as detail_file:
                detail_file.write(rst.encode("utf-8"))

        if self.app.config.autoapi_add_toctree_entry:
            self._output_top_rst(root)

    def _output_top_rst(self, root):
        # Render Top Index
        top_level_index = os.path.join(root, "index.rst")
        pages = self.objects.values()
        with open(top_level_index, "wb") as top_level_file:
            content = self.jinja_env.get_template("index.rst")
            top_level_file.write(content.render(pages=pages).encode("utf-8"))
