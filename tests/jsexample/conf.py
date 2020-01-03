# -*- coding: utf-8 -*-

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = u"jsexample"
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
htmlhelp_basename = "jsexampledoc"
extensions = ["autoapi.extension"]
autoapi_type = "javascript"
autoapi_dirs = ["example"]
autoapi_file_pattern = "*.js"
