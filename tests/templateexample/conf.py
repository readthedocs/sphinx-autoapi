# -*- coding: utf-8 -*-

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'pyexample'
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
htmlhelp_basename = 'pyexampledoc'
extensions = ['autoapi.extension']
autoapi_type = 'python'
autoapi_dir = 'example'
autoapi_file_pattern = '*.py'
autoapi_template_dir = 'template_overrides'
autoapi_keep_files = False

exclude_patterns = [autoapi_template_dir]