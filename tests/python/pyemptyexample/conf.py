# -*- coding: utf-8 -*-

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "pyexample"
copyright = "2015, readthedocs"
author = "readthedocs"
version = "0.1"
release = "0.1"
language = "en"
exclude_patterns = ["_build"]
pygments_style = "sphinx"
todo_include_todos = False
html_theme = "alabaster"
htmlhelp_basename = "pyexampledoc"
extensions = ["sphinx.ext.autodoc", "autoapi.extension"]
autoapi_dirs = ["example"]
autoapi_python_class_content = "both"
autoapi_options = [
    "members",
    "undoc-members",  # this is temporary until we add docstrings across the codebase
    "show-inheritance",
    "show-module-summary",
    "special-members",
    "imported-members",
    "inherited-members",
]
