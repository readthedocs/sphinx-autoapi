"""Sphinx Auto-API Top-level Extension.

This extension allows you to automagically generate API documentation from your project.
"""
import io
import os
import shutil
from typing import Dict, Tuple
import warnings

import sphinx
from sphinx.util.console import colorize
from sphinx.addnodes import toctree
from sphinx.errors import ExtensionError
import sphinx.util.logging
from docutils.parsers.rst import directives

from . import documenters
from .directives import AutoapiSummary, NestedParse
from .inheritance_diagrams import AutoapiInheritanceDiagram
from .mappers import PythonSphinxMapper
from .settings import API_ROOT

LOGGER = sphinx.util.logging.getLogger(__name__)

_DEFAULT_FILE_PATTERNS = ["*.py", "*.pyi"]
_DEFAULT_IGNORE_PATTERNS = ["*migrations*"]
_DEFAULT_OPTIONS = [
    "members",
    "undoc-members",
    "private-members",
    "show-inheritance",
    "show-module-summary",
    "special-members",
    "imported-members",
]
_VIEWCODE_CACHE: Dict[str, Tuple[str, Dict]] = {}
"""Caches a module's parse results for use in viewcode."""


class RemovedInAutoAPI3Warning(DeprecationWarning):
    """Indicates something that will be removed in sphinx-autoapi v3."""


if "PYTHONWARNINGS" not in os.environ:
    warnings.filterwarnings("default", category=RemovedInAutoAPI3Warning)


def _normalise_autoapi_dirs(autoapi_dirs, srcdir):
    normalised_dirs = []

    if isinstance(autoapi_dirs, str):
        autoapi_dirs = [autoapi_dirs]
    for path in autoapi_dirs:
        if os.path.isabs(path):
            normalised_dirs.append(path)
        else:
            normalised_dirs.append(os.path.normpath(os.path.join(srcdir, path)))

    return normalised_dirs


def run_autoapi(app):
    """Load AutoAPI data from the filesystem."""
    if not app.config.autoapi_dirs:
        raise ExtensionError("You must configure an autoapi_dirs setting")

    if app.config.autoapi_include_summaries is not None:
        warnings.warn(
            "autoapi_include_summaries has been replaced by "
            "the show-module-summary AutoAPI option\n",
            RemovedInAutoAPI3Warning,
        )
        if app.config.autoapi_include_summaries:
            app.config.autoapi_options.append("show-module-summary")

    # Make sure the paths are full
    normalised_dirs = _normalise_autoapi_dirs(app.config.autoapi_dirs, app.srcdir)
    for _dir in normalised_dirs:
        if not os.path.exists(_dir):
            raise ExtensionError(
                f"AutoAPI Directory `{_dir}` not found. "
                "Please check your `autoapi_dirs` setting."
            )

    normalized_root = os.path.normpath(
        os.path.join(app.srcdir, app.config.autoapi_root)
    )
    url_root = os.path.join("/", app.config.autoapi_root)

    template_dir = app.config.autoapi_template_dir
    if template_dir and not os.path.isabs(template_dir):
        if not os.path.isdir(template_dir):
            template_dir = os.path.join(app.srcdir, app.config.autoapi_template_dir)
        elif app.srcdir != os.getcwd():
            warnings.warn(
                "autoapi_template_dir will be expected to be "
                "relative to the Sphinx source directory instead of "
                "relative to where sphinx-build is run\n",
                RemovedInAutoAPI3Warning,
            )
    sphinx_mapper_obj = PythonSphinxMapper(
        app, template_dir=template_dir, url_root=url_root
    )

    if app.config.autoapi_file_patterns:
        file_patterns = app.config.autoapi_file_patterns
    else:
        file_patterns = _DEFAULT_FILE_PATTERNS

    if app.config.autoapi_ignore:
        ignore_patterns = app.config.autoapi_ignore
    else:
        ignore_patterns = _DEFAULT_IGNORE_PATTERNS

    if ".rst" in app.config.source_suffix:
        out_suffix = ".rst"
    elif ".txt" in app.config.source_suffix:
        out_suffix = ".txt"
    else:
        # Fallback to first suffix listed
        out_suffix = next(iter(app.config.source_suffix))

    if sphinx_mapper_obj.load(
        patterns=file_patterns, dirs=normalised_dirs, ignore=ignore_patterns
    ):
        sphinx_mapper_obj.map(options=app.config.autoapi_options)

        if app.config.autoapi_generate_api_docs:
            sphinx_mapper_obj.output_rst(root=normalized_root, source_suffix=out_suffix)


def build_finished(app, exception):
    if not app.config.autoapi_keep_files and app.config.autoapi_generate_api_docs:
        normalized_root = os.path.normpath(
            os.path.join(app.srcdir, app.config.autoapi_root)
        )
        if app.verbosity > 1:
            LOGGER.info(
                colorize("bold", "[AutoAPI] ")
                + colorize("darkgreen", "Cleaning generated .rst files")
            )
        shutil.rmtree(normalized_root)


def source_read(app, docname, source):
    # temp_data is cleared after each source file has been processed,
    # so populate the annotations at the beginning of every file read.
    app.env.temp_data["annotations"] = getattr(app.env, "autoapi_annotations", {})


def doctree_read(app, doctree):
    """Inject AutoAPI into the TOC Tree dynamically."""

    if app.env.docname == "index":
        all_docs = set()
        insert = True
        nodes = list(doctree.traverse(toctree))
        toc_entry = f"{app.config.autoapi_root}/index"
        add_entry = (
            nodes
            and app.config.autoapi_generate_api_docs
            and app.config.autoapi_add_toctree_entry
        )
        if not add_entry:
            return
        # Capture all existing toctree entries
        for node in nodes:
            for entry in node["entries"]:
                all_docs.add(entry[1])
        # Don't insert autoapi it's already present
        for doc in all_docs:
            if doc.find(app.config.autoapi_root) != -1:
                insert = False
        if insert and app.config.autoapi_add_toctree_entry:
            # Insert AutoAPI index
            nodes[-1]["entries"].append((None, toc_entry))
            nodes[-1]["includefiles"].append(toc_entry)
            message_prefix = colorize("bold", "[AutoAPI] ")
            message = colorize(
                "darkgreen", f"Adding AutoAPI TOCTree [{toc_entry}] to index.rst"
            )
            LOGGER.info(message_prefix + message)


def viewcode_find(app, modname):
    objects = app.env.autoapi_objects
    if modname not in objects:
        return None

    if modname in _VIEWCODE_CACHE:
        return _VIEWCODE_CACHE[modname]

    locations = {}
    module = objects[modname]
    for child in module.children:
        stack = [("", child)]
        while stack:
            prefix, obj = stack.pop()
            type_ = "other"
            if obj.type == "class":
                type_ = "class"
            elif obj.type in ("function", "method"):
                type_ = "def"
            full_name = prefix + obj.name
            if "from_line_no" in obj.obj:
                locations[full_name] = (
                    type_,
                    obj.obj["from_line_no"],
                    obj.obj["to_line_no"],
                )
            children = getattr(obj, "children", ())
            stack.extend((full_name + ".", gchild) for gchild in children)

    if module.obj["encoding"]:
        stream = io.open(module.obj["file_path"], encoding=module.obj["encoding"])
    else:
        stream = open(module.obj["file_path"], encoding="utf-8")

    with stream as in_f:
        source = in_f.read()

    result = (source, locations)
    _VIEWCODE_CACHE[modname] = result
    return result


def viewcode_follow_imported(app, modname, attribute):
    fullname = f"{modname}.{attribute}"
    all_objects = app.env.autoapi_all_objects
    if fullname not in all_objects:
        return None

    if all_objects[fullname].obj.get("type") == "method":
        fullname = fullname[: fullname.rfind(".")]
        attribute = attribute[: attribute.rfind(".")]
    while all_objects[fullname].obj.get("original_path", "") != "":
        fullname = all_objects[fullname].obj.get("original_path")

    orig_path = fullname
    if orig_path.endswith(attribute):
        return orig_path[: -len(attribute) - 1]

    return modname


def setup(app):
    app.connect("builder-inited", run_autoapi)
    app.connect("source-read", source_read)
    # Use a lower priority than the default to ensure that we can
    # inject into the toctree before Sphinx tries to use it
    # in another doctree-read transformer.
    app.connect("doctree-read", doctree_read, priority=400)
    app.connect("build-finished", build_finished)
    if "viewcode-find-source" in app.events.events:
        app.connect("viewcode-find-source", viewcode_find)
    if "viewcode-follow-imported" in app.events.events:
        app.connect("viewcode-follow-imported", viewcode_follow_imported)
    app.add_config_value("autoapi_root", API_ROOT, "html")
    app.add_config_value("autoapi_ignore", [], "html")
    app.add_config_value("autoapi_options", _DEFAULT_OPTIONS, "html")
    app.add_config_value("autoapi_member_order", "bysource", "html")
    app.add_config_value("autoapi_file_patterns", None, "html")
    app.add_config_value("autoapi_dirs", [], "html")
    app.add_config_value("autoapi_keep_files", False, "html")
    app.add_config_value("autoapi_add_toctree_entry", True, "html")
    app.add_config_value("autoapi_template_dir", None, "html")
    app.add_config_value("autoapi_include_summaries", None, "html")
    app.add_config_value("autoapi_python_use_implicit_namespaces", False, "html")
    app.add_config_value("autoapi_python_class_content", "class", "html")
    app.add_config_value("autoapi_generate_api_docs", True, "html")
    app.add_config_value("autoapi_prepare_jinja_env", None, "html")
    app.add_config_value("autoapi_own_page_level", "module", "html")
    app.add_autodocumenter(documenters.AutoapiFunctionDocumenter)
    app.add_autodocumenter(documenters.AutoapiPropertyDocumenter)
    app.add_autodocumenter(documenters.AutoapiDecoratorDocumenter)
    app.add_autodocumenter(documenters.AutoapiClassDocumenter)
    app.add_autodocumenter(documenters.AutoapiMethodDocumenter)
    app.add_autodocumenter(documenters.AutoapiDataDocumenter)
    app.add_autodocumenter(documenters.AutoapiAttributeDocumenter)
    app.add_autodocumenter(documenters.AutoapiModuleDocumenter)
    app.add_autodocumenter(documenters.AutoapiExceptionDocumenter)
    directives.register_directive("autoapi-nested-parse", NestedParse)
    directives.register_directive("autoapisummary", AutoapiSummary)
    app.setup_extension("sphinx.ext.autosummary")
    app.add_event("autoapi-skip-member")
    app.setup_extension("sphinx.ext.inheritance_diagram")
    app.add_directive("autoapi-inheritance-diagram", AutoapiInheritanceDiagram)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
