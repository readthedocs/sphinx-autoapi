# -*- coding: utf-8 -*-

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'dotnetexample'
copyright = u'2015, rtfd'
author = u'rtfd'
version = '0.1'
release = '0.1'
language = None
exclude_patterns = ['_build']
pygments_style = 'sphinx'
todo_include_todos = False
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
htmlhelp_basename = 'dotnetexampledoc'
extensions = ['autoapi.extension', 'sphinxcontrib.dotnetdomain']

autoapi_type = 'dotnet'
autoapi_dir = 'example/corefx/src'
autoapi_ignore = ['*toc.yml', '*index.yml', '*tests*tests*']
