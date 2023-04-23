# -*- coding: utf-8 -*-

templates_path = ["_templates"]
source_suffix = {".md": "markdown"}
master_doc = "index"
project = "pymarkdownexample"
copyright = "2015, readthedocs"
author = "readthedocs"
version = "0.1"
release = "0.1"
language = "en"
exclude_patterns = ["_build"]
pygments_style = "sphinx"
todo_include_todos = False
html_theme = "alabaster"
htmlhelp_basename = "pymarkdownexampledoc"
extensions = ["myst_parser", "sphinx.ext.autodoc", "autoapi.extension"]
myst_enable_extensions = ["colon_fence", "fieldlist"]
autoapi_type = "python"
autoapi_dirs = ["example"]
autoapi_file_pattern = "*.py"
autoapi_python_class_content = "both"
autoapi_keep_files = True
