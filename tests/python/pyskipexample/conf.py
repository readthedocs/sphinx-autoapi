# -*- coding: utf-8 -*-

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = u"pyexample"
copyright = u"2015, readthedocs"
author = u"readthedocs"
version = "0.1"
release = "0.1"
language = None
exclude_patterns = ["_build"]
pygments_style = "sphinx"
todo_include_todos = False
html_theme = "alabaster"
html_static_path = ["_static"]
htmlhelp_basename = "pyexampledoc"
extensions = ["sphinx.ext.autodoc", "autoapi.extension"]
autoapi_type = "python"
autoapi_dirs = ["example"]
autoapi_file_pattern = "*.py"
autoapi_options = ["members", "undoc-members", "special-members"]
SKIP = {"example.foo", "example.Bar", "example.Bar.m", "example.Baf.m", "example.baz"}


def maybe_skip_member(app, what, name, obj, skip, options):
    return name in SKIP


def setup(app):
    app.connect("autoapi-skip-member", maybe_skip_member)
