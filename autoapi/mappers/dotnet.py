import re
import os
import subprocess
import traceback
import shutil
from collections import defaultdict
import unidecode

import yaml
from sphinx.util.osutil import ensuredir
from sphinx.util.console import darkgreen, bold
import sphinx.util.logging
from sphinx.errors import ExtensionError

from .base import PythonMapperBase, SphinxMapperBase

LOGGER = sphinx.util.logging.getLogger(__name__)

# Doc comment patterns
DOC_COMMENT_PATTERN = r"""
    \<%(tag)s
    \s+%(attr)s="(?P<attr_value>[^"]*?)"
    \s*?
    (?:
        \/\>|
        \>(?P<inner>[^\<]*?)\<\/%(tag)s\>
    )
"""
DOC_COMMENT_SEE_PATTERN = re.compile(
    DOC_COMMENT_PATTERN % {"tag": "(?:see|seealso)", "attr": "cref"}, re.X
)
DOC_COMMENT_PARAM_PATTERN = re.compile(
    DOC_COMMENT_PATTERN % {"tag": "(?:paramref|typeparamref)", "attr": "name"}, re.X
)

# Comment member identities
# From: https://msdn.microsoft.com/en-us/library/vstudio/fsbx0t7x(v=VS.100).aspx
DOC_COMMENT_IDENTITIES = {
    "N": "dn:ns",
    "T": "any",  # can be any type (class, delegate, enum, etc), so use any
    "F": "dn:field",
    "P": "dn:prop",
    "M": "dn:meth",
    "E": "dn:event",
}


class DotNetSphinxMapper(SphinxMapperBase):

    """Auto API domain handler for .NET

    Searches for YAML files, and soon to be JSON files as well, for auto API
    sources. If no pattern configuration was explicitly specified, then default
    to looking up a ``docfx.json`` file.

    :param app: Sphinx application passed in as part of the extension
    """

    top_namespaces = {}

    DOCFX_OUTPUT_PATH = "_api"

    # pylint: disable=arguments-differ
    def load(self, patterns, dirs, ignore=None, **kwargs):
        """Load objects from the filesystem into the ``paths`` dictionary.

        If the setting ``autoapi_patterns`` was not specified, look for a
        ``docfx.json`` file by default.  A ``docfx.json`` should be treated as
        the canonical source before the default patterns.  Fallback to default
        pattern matches if no ``docfx.json`` files are found.
        """
        raise_error = kwargs.get("raise_error", True)
        all_files = set()
        if not self.app.config.autoapi_file_patterns:
            all_files = set()
            for _file in self.find_files(
                patterns=["docfx.json"], dirs=dirs, ignore=ignore
            ):
                all_files.add(_file)
        if not all_files:
            for _file in self.find_files(patterns=patterns, dirs=dirs, ignore=ignore):
                all_files.add(_file)
        if all_files:
            try:
                command = ["docfx", "metadata", "--raw", "--force"]
                command.extend(all_files)
                proc = subprocess.Popen(
                    " ".join(command),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    env=dict(
                        (key, os.environ[key])
                        for key in [
                            "PATH",
                            "HOME",
                            "SYSTEMROOT",
                            "USERPROFILE",
                            "WINDIR",
                        ]
                        if key in os.environ
                    ),
                )
                _, error_output = proc.communicate()
                if error_output:
                    LOGGER.warning(error_output)
            except (OSError, subprocess.CalledProcessError) as e:
                LOGGER.warning("Error generating metadata: {0}".format(e))
                if raise_error:
                    raise ExtensionError(
                        "Failure in docfx while generating AutoAPI output."
                    )
        # We now have yaml files
        for xdoc_path in self.find_files(
            patterns=["*.yml"], dirs=[self.DOCFX_OUTPUT_PATH], ignore=ignore
        ):
            data = self.read_file(path=xdoc_path)
            if data:
                self.paths[xdoc_path] = data

    def read_file(self, path, **kwargs):
        """Read file input into memory, returning deserialized objects

        :param path: Path of file to read
        """
        try:
            with open(path, "r") as handle:
                parsed_data = yaml.safe_load(handle)
                return parsed_data
        except IOError:
            LOGGER.warning("Error reading file: {0}".format(path))
        except TypeError:
            LOGGER.warning("Error reading file: {0}".format(path))
        return None

    # Subclassed to iterate over items
    def map(self, options=None):
        """Trigger find of serialized sources and build objects"""
        for path, data in self.paths.items():
            references = data.get("references", [])
            for item in data["items"]:
                for obj in self.create_class(item, options, references=references):
                    self.add_object(obj)

        self.organize_objects()

    def create_class(self, data, options=None, path=None, **kwargs):
        """
        Return instance of class based on Roslyn type property

        Data keys handled here:

            type
                Set the object class

            items
                Recurse into :py:meth:`create_class` to create child object
                instances

        :param data: dictionary data from Roslyn output artifact
        """

        obj_map = dict((cls.type, cls) for cls in ALL_CLASSES)
        try:
            cls = obj_map[data["type"].lower()]
        except KeyError:
            LOGGER.warning("Unknown type: %s" % data)
        else:
            obj = cls(
                data,
                jinja_env=self.jinja_env,
                options=options,
                url_root=self.url_root,
                **kwargs
            )

            # Append child objects
            # TODO this should recurse in the case we're getting back more
            # complex argument listings

            yield obj

    def add_object(self, obj):
        """Add object to local and app environment storage

        :param obj: Instance of a .NET object
        """
        if obj.top_level_object:
            if isinstance(obj, DotNetNamespace):
                self.namespaces[obj.name] = obj
        self.objects[obj.id] = obj

    def organize_objects(self):
        """Organize objects and namespaces"""

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
                    for ns_obj in self.create_class(
                        {"uid": namespace, "type": "namespace"}
                    ):
                        self.top_namespaces[ns_obj.id] = ns_obj
                if obj not in ns_obj.children and namespace != obj.id:
                    ns_obj.children.append(obj)

        for obj in self.objects.values():
            _render_children(obj)
            _recurse_ns(obj)

        # Clean out dead namespaces
        for key, ns in self.top_namespaces.copy().items():
            if not ns.children:
                del self.top_namespaces[key]

        for key, ns in self.namespaces.items():
            if not ns.children:
                del self.namespaces[key]

    def output_rst(self, root, source_suffix):
        if not self.objects:
            raise ExtensionError("No API objects exist. Can't continue")
        for id, obj in self.objects.items():

            if not obj or not obj.top_level_object:
                continue

            rst = obj.render()
            if not rst:
                continue

            detail_dir = os.path.join(root, obj.pathname)
            ensuredir(detail_dir)
            path = os.path.join(detail_dir, "%s%s" % ("index", source_suffix))
            with open(path, "wb") as detail_file:
                detail_file.write(rst.encode("utf-8"))

        # Render Top Index
        top_level_index = os.path.join(root, "index.rst")
        with open(top_level_index, "wb") as top_level_file:
            content = self.jinja_env.get_template("index.rst")
            top_level_file.write(
                content.render(pages=self.namespaces.values()).encode("utf-8")
            )

    @staticmethod
    def build_finished(app, exception):
        if app.verbosity > 1:
            LOGGER.info(bold("[AutoAPI] ") + darkgreen("Cleaning generated .yml files"))
        if os.path.exists(DotNetSphinxMapper.DOCFX_OUTPUT_PATH):
            shutil.rmtree(DotNetSphinxMapper.DOCFX_OUTPUT_PATH)


class DotNetPythonMapper(PythonMapperBase):

    """Base .NET object representation

    :param references: object reference list from docfx
    :type references: list of dict objects
    """

    language = "dotnet"

    def __init__(self, obj, **kwargs):
        self.references = dict(
            (obj.get("uid"), obj)
            for obj in kwargs.pop("references", [])
            if "uid" in obj
        )
        super(DotNetPythonMapper, self).__init__(obj, **kwargs)

        # Always exist
        self.id = obj.get("uid", obj.get("id"))
        self.definition = obj.get("definition", self.id)
        self.name = obj.get("fullName", self.definition)

        # Optional
        self.fullname = obj.get("fullName")
        self.summary = self.transform_doc_comments(obj.get("summary", ""))
        self.parameters = []
        self.items = obj.get("items", [])
        self.children_strings = obj.get("children", [])
        self.children = []
        self.item_map = defaultdict(list)
        self.inheritance = []
        self.assemblies = obj.get("assemblies", [])

        # Syntax example and parameter list
        syntax = obj.get("syntax", None)
        self.example = ""
        if syntax is not None:
            # Code example
            try:
                self.example = syntax["content"]
            except (KeyError, TypeError):
                traceback.print_exc()

            self.parameters = []
            for param in syntax.get("parameters", []):
                if "id" in param:
                    self.parameters.append(
                        {
                            "name": param.get("id"),
                            "type": self.resolve_spec_identifier(param.get("type")),
                            "desc": self.transform_doc_comments(
                                param.get("description", "")
                            ),
                        }
                    )

            self.returns = {}
            self.returns["type"] = self.resolve_spec_identifier(
                syntax.get("return", {}).get("type")
            )
            self.returns["description"] = self.transform_doc_comments(
                syntax.get("return", {}).get("description")
            )

        # Inheritance
        # TODO Support more than just a class type here, should support enum/etc
        self.inheritance = [
            DotNetClass({"uid": name, "name": name})
            for name in obj.get("inheritance", [])
        ]

    def __str__(self):
        return "<{cls} {id}>".format(cls=self.__class__.__name__, id=self.id)

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
        try:
            slug = self.name.split("(")[0]
        except IndexError:
            pass
        slug = unidecode.unidecode(slug)
        slug = slug.replace("-", "")
        slug = re.sub(r"[^\w\.]+", "-", slug).strip("-")
        return os.path.join(*slug.split("."))

    @property
    def short_name(self):
        """Shorten name property"""
        return self.name.split(".")[-1]

    @property
    def edit_link(self):
        try:
            repo = self.source["remote"]["repo"].replace(".git", "")
            path = self.path
            return "{repo}/blob/master/{path}".format(repo=repo, path=path)
        except Exception:
            return ""

    @property
    def source(self):
        return self.obj.get("source")

    @property
    def path(self):
        return self.source["path"]

    @property
    def namespace(self):
        pieces = self.id.split(".")[:-1]
        if pieces:
            return ".".join(pieces)
        return None

    @property
    def top_namespace(self):
        pieces = self.id.split(".")[:2]
        if pieces:
            return ".".join(pieces)
        return None

    @property
    def ref_type(self):
        return self.type

    @property
    def ref_directive(self):
        return self.type

    @property
    def ref_name(self):
        """Return object name suitable for use in references

        Escapes several known strings that cause problems, including the
        following reference syntax::

            :dotnet:cls:`Foo.Bar<T>`

        As the `<T>` notation is also special syntax in references, indicating
        the reference to Foo.Bar should be named T.

        See: http://sphinx-doc.org/domains.html#role-cpp:any
        """
        return self.name.replace("<", "\<").replace("`", "\`")

    @property
    def ref_short_name(self):
        """Same as above, return the truncated name instead"""
        return self.ref_name.split(".")[-1]

    @staticmethod
    def transform_doc_comments(text):
        """
        Parse XML content for references and other syntax.

        This avoids an LXML dependency, we only need to parse out a small subset
        of elements here. Iterate over string to reduce regex pattern complexity
        and make substitutions easier

        .. seealso::

            `Doc comment reference <https://msdn.microsoft.com/en-us/library/5ast78ax.aspx>`
                Reference on XML documentation comment syntax
        """
        try:
            while True:
                found = DOC_COMMENT_SEE_PATTERN.search(text)
                if found is None:
                    break
                ref = found.group("attr_value").replace("<", "\<").replace("`", "\`")

                reftype = "any"
                replacement = ""
                # Given the pattern of `\w:\w+`, inspect first letter of
                # reference for identity type
                if ref[1] == ":" and ref[0] in DOC_COMMENT_IDENTITIES:
                    reftype = DOC_COMMENT_IDENTITIES[ref[:1]]
                    ref = ref[2:]
                    replacement = ":{reftype}:`{ref}`".format(reftype=reftype, ref=ref)
                elif ref[:2] == "!:":
                    replacement = ref[2:]
                else:
                    replacement = ":any:`{ref}`".format(ref=ref)

                # Escape following text
                text_end = text[found.end() :]
                text_start = text[: found.start()]
                text_end = re.sub(r"^(\S)", r"\\\1", text_end)
                text_start = re.sub(r"(\S)$", r"\1 ", text_start)

                text = "".join([text_start, replacement, text_end])
            while True:
                found = DOC_COMMENT_PARAM_PATTERN.search(text)
                if found is None:
                    break

                # Escape following text
                text_end = text[found.end() :]
                text_start = text[: found.start()]
                text_end = re.sub(r"^(\S)", r"\\\1", text_end)
                text_start = re.sub(r"(\S)$", r"\1 ", text_start)

                text = "".join(
                    [text_start, "``", found.group("attr_value"), "``", text_end]
                )
        except TypeError:
            pass
        return text

    def resolve_spec_identifier(self, obj_name):
        """Find reference name based on spec identifier

        Spec identifiers are used in parameter and return type definitions, but
        should be a user-friendly version instead. Use docfx ``references``
        lookup mapping for resolution.

        If the spec identifier reference has a ``spec.csharp`` key, this implies
        a compound reference that should be linked in a special way. Resolve to
        a nested reference, with the corrected nodes.

        .. note::
            This uses a special format that is interpreted by the domain for
            parameter type and return type fields.

        :param obj_name: spec identifier to resolve to a correct reference
        :returns: resolved string with one or more references
        :rtype: str
        """
        ref = self.references.get(obj_name)
        if ref is None:
            return obj_name

        resolved = ref.get("fullName", obj_name)
        spec = ref.get("spec.csharp", [])
        parts = []
        for part in spec:
            if part.get("name") == "<":
                parts.append("{")
            elif part.get("name") == ">":
                parts.append("}")
            elif "fullName" in part and "uid" in part:
                parts.append("{fullName}<{uid}>".format(**part))
            elif "uid" in part:
                parts.append(part["uid"])
            elif "fullName" in part:
                parts.append(part["fullName"])
        if parts:
            resolved = "".join(parts)
        return resolved


class DotNetNamespace(DotNetPythonMapper):
    type = "namespace"
    ref_directive = "ns"
    plural = "namespaces"
    top_level_object = True


class DotNetMethod(DotNetPythonMapper):
    type = "method"
    ref_directive = "meth"
    plural = "methods"


class DotNetOperator(DotNetPythonMapper):
    type = "operator"
    ref_directive = "op"
    plural = "operators"


class DotNetProperty(DotNetPythonMapper):
    type = "property"
    ref_directive = "prop"
    plural = "properties"


class DotNetEnum(DotNetPythonMapper):
    type = "enum"
    ref_type = "enumeration"
    ref_directive = "enum"
    plural = "enumerations"
    top_level_object = True


class DotNetStruct(DotNetPythonMapper):
    type = "struct"
    ref_type = "structure"
    ref_directive = "struct"
    plural = "structures"
    top_level_object = True


class DotNetConstructor(DotNetPythonMapper):
    type = "constructor"
    ref_directive = "ctor"
    plural = "constructors"


class DotNetInterface(DotNetPythonMapper):
    type = "interface"
    ref_directive = "iface"
    plural = "interfaces"
    top_level_object = True


class DotNetDelegate(DotNetPythonMapper):
    type = "delegate"
    ref_directive = "del"
    plural = "delegates"
    top_level_object = True


class DotNetClass(DotNetPythonMapper):
    type = "class"
    ref_directive = "cls"
    plural = "classes"
    top_level_object = True


class DotNetField(DotNetPythonMapper):
    type = "field"
    plural = "fields"


class DotNetEvent(DotNetPythonMapper):
    type = "event"
    plural = "events"


ALL_CLASSES = [
    DotNetNamespace,
    DotNetClass,
    DotNetEnum,
    DotNetStruct,
    DotNetInterface,
    DotNetDelegate,
    DotNetOperator,
    DotNetProperty,
    DotNetMethod,
    DotNetConstructor,
    DotNetField,
    DotNetEvent,
]
