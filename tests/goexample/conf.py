# -*- coding: utf-8 -*-

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'goexample'
copyright = u'2015, rtfd'
author = u'rtfd'
version = '0.1'
release = '0.1'
language = None
exclude_patterns = ['_build']
pygments_style = 'sphinx'
todo_include_todos = False
html_theme = 'alabaster'
html_static_path = ['_static']
htmlhelp_basename = 'goexampledoc'
extensions = ['autoapi.extension', 'sphinxcontrib.golangdomain']

autoapi_type = 'go'
autoapi_dir = 'example'
autoapi_file_pattern = '*.go'
