# -*- coding: utf-8 -*-
"""
Sphinx Auto-API Top-level Extension.

This extension allows you to automagically generate API documentation from your project.
"""
import codecs
import os
import shutil

import sphinx
from sphinx.util.console import darkgreen, bold
from sphinx.addnodes import toctree
from sphinx.errors import ExtensionError
import sphinx.util.logging
from docutils.parsers.rst import directives

from . import documenters
from . import utils
from .backends import (
    default_file_mapping,
    default_ignore_patterns,
    default_backend_mapping,
)
from .directives import AutoapiSummary, NestedParse
from .settings import API_ROOT
from .toctree import add_domain_to_toctree

LOGGER = sphinx.util.logging.getLogger(__name__)

default_options = ["members", "undoc-members", "private-members", "special-members"]
_viewcode_cache = {}
"""Caches a module's parse results for use in viewcode.

:type: dict(str, tuple)
"""


def run_autoapi(app):
    """
    Load AutoAPI data from the filesystem.
    """

    if not app.config.autoapi_dirs:
        raise ExtensionError("You must configure an autoapi_dirs setting")

    # Make sure the paths are full
    normalized_dirs = []
    autoapi_dirs = app.config.autoapi_dirs
    if isinstance(autoapi_dirs, str):
        autoapi_dirs = [autoapi_dirs]
    for path in autoapi_dirs:
        if os.path.isabs(path):
            normalized_dirs.append(path)
        else:
            normalized_dirs.append(os.path.normpath(os.path.join(app.confdir, path)))

    for _dir in normalized_dirs:
        if not os.path.exists(_dir):
            raise ExtensionError(
                "AutoAPI Directory `{dir}` not found. "
                "Please check your `autoapi_dirs` setting.".format(dir=_dir)
            )

    normalized_root = os.path.normpath(
        os.path.join(app.confdir, app.config.autoapi_root)
    )
    url_root = os.path.join("/", app.config.autoapi_root)

    sphinx_mapper = default_backend_mapping[app.config.autoapi_type]
    sphinx_mapper_obj = sphinx_mapper(
        app, template_dir=app.config.autoapi_template_dir, url_root=url_root
    )
    app.env.autoapi_mapper = sphinx_mapper_obj

    if app.config.autoapi_file_patterns:
        file_patterns = app.config.autoapi_file_patterns
    else:
        file_patterns = default_file_mapping.get(app.config.autoapi_type, [])

    if app.config.autoapi_ignore:
        ignore_patterns = app.config.autoapi_ignore
    else:
        ignore_patterns = default_ignore_patterns.get(app.config.autoapi_type, [])

    if ".rst" in app.config.source_suffix:
        out_suffix = ".rst"
    elif ".txt" in app.config.source_suffix:
        out_suffix = ".txt"
    else:
        # Fallback to first suffix listed
        out_suffix = app.config.source_suffix[0]

    # Actual meat of the run.
    LOGGER.info(bold("[AutoAPI] ") + darkgreen("Loading Data"))
    sphinx_mapper_obj.load(
        patterns=file_patterns, dirs=normalized_dirs, ignore=ignore_patterns
    )

    LOGGER.info(bold("[AutoAPI] ") + darkgreen("Mapping Data"))
    sphinx_mapper_obj.map(options=app.config.autoapi_options)

    if app.config.autoapi_generate_api_docs:
        LOGGER.info(bold("[AutoAPI] ") + darkgreen("Rendering Data"))
        sphinx_mapper_obj.output_rst(root=normalized_root, source_suffix=out_suffix)


def build_finished(app, exception):
    if not app.config.autoapi_keep_files and app.config.autoapi_generate_api_docs:
        normalized_root = os.path.normpath(
            os.path.join(app.confdir, app.config.autoapi_root)
        )
        if app.verbosity > 1:
            LOGGER.info(bold("[AutoAPI] ") + darkgreen("Cleaning generated .rst files"))
        shutil.rmtree(normalized_root)

        sphinx_mapper = default_backend_mapping[app.config.autoapi_type]
        if hasattr(sphinx_mapper, "build_finished"):
            sphinx_mapper.build_finished(app, exception)


def doctree_read(app, doctree):
    """
    Inject AutoAPI into the TOC Tree dynamically.
    """
    if app.env.docname == "index":
        all_docs = set()
        insert = True
        nodes = doctree.traverse(toctree)
        toc_entry = "%s/index" % app.config.autoapi_root
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
            nodes[-1]["entries"].append((None, u"%s/index" % app.config.autoapi_root))
            nodes[-1]["includefiles"].append(u"%s/index" % app.config.autoapi_root)
            message_prefix = bold("[AutoAPI] ")
            message = darkgreen(
                "Adding AutoAPI TOCTree [{0}] to index.rst".format(toc_entry)
            )
            LOGGER.info(message_prefix + message)


def clear_env(app, env):
    """Clears the environment of the unpicklable objects that we left behind."""
    env.autoapi_mapper = None


def viewcode_find(app, modname):
    mapper = app.env.autoapi_mapper
    if modname not in mapper.objects:
        return None

    if modname in _viewcode_cache:
        return _viewcode_cache[modname]

    locations = {}
    module = mapper.objects[modname]
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
        source = codecs.open(
            module.obj["file_path"], encoding=module.obj["encoding"]
        ).read()
    else:
        source = open(module.obj["file_path"]).read()

    result = (source, locations)
    _viewcode_cache[modname] = result
    return result


def viewcode_follow_imported(app, modname, attribute):
    fullname = "{}.{}".format(modname, attribute)
    mapper = app.env.autoapi_mapper
    if fullname not in mapper.all_objects:
        return None

    orig_path = mapper.all_objects[fullname].obj.get("original_path", "")
    if orig_path.endswith(attribute):
        return orig_path[: -len(attribute) - 1]

    return modname


def setup(app):
    app.connect("builder-inited", run_autoapi)
    app.connect("doctree-read", doctree_read)
    app.connect("doctree-resolved", add_domain_to_toctree)
    app.connect("build-finished", build_finished)
    app.connect("env-updated", clear_env)
    if sphinx.version_info >= (1, 8):
        if "viewcode-find-source" in app.events.events:
            app.connect("viewcode-find-source", viewcode_find)
        if "viewcode-follow-imported" in app.events.events:
            app.connect("viewcode-follow-imported", viewcode_follow_imported)
    app.add_config_value("autoapi_type", "python", "html")
    app.add_config_value("autoapi_root", API_ROOT, "html")
    app.add_config_value("autoapi_ignore", [], "html")
    app.add_config_value("autoapi_options", default_options, "html")
    app.add_config_value("autoapi_file_patterns", None, "html")
    app.add_config_value("autoapi_dirs", [], "html")
    app.add_config_value("autoapi_keep_files", False, "html")
    app.add_config_value("autoapi_add_toctree_entry", True, "html")
    app.add_config_value("autoapi_template_dir", None, "html")
    app.add_config_value("autoapi_include_summaries", False, "html")
    app.add_config_value("autoapi_python_class_content", "class", "html")
    app.add_config_value("autoapi_generate_api_docs", True, "html")
    app.add_autodocumenter(documenters.AutoapiFunctionDocumenter)
    app.add_autodocumenter(documenters.AutoapiClassDocumenter)
    app.add_autodocumenter(documenters.AutoapiMethodDocumenter)
    app.add_autodocumenter(documenters.AutoapiDataDocumenter)
    app.add_autodocumenter(documenters.AutoapiAttributeDocumenter)
    app.add_autodocumenter(documenters.AutoapiModuleDocumenter)
    app.add_autodocumenter(documenters.AutoapiExceptionDocumenter)
    directives.register_directive("autoapi-nested-parse", NestedParse)
    directives.register_directive("autoapisummary", AutoapiSummary)
    app.setup_extension("sphinx.ext.autosummary")
