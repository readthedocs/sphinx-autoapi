# -*- coding: utf-8 -*-

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "pypackageexample"
copyright = "2015, readthedocs"
author = "readthedocs"
version = "0.1"
release = "0.1"
language = "en"
exclude_patterns = ["_build"]
pygments_style = "sphinx"
todo_include_todos = False
html_theme = "alabaster"
htmlhelp_basename = "pypackageexampledoc"
extensions = ["autoapi.extension"]
autoapi_dirs = ["example"]
autoapi_file_pattern = "*.py"
autoapi_keep_files = True
