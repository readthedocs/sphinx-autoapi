# -*- coding: utf-8 -*-

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = u"dotnetexample"
copyright = u"2015, readthedocs"
author = u"readthedocs"
version = "0.1"
release = "0.1"
language = None
exclude_patterns = ["_build"]
pygments_style = "sphinx"
todo_include_todos = False
html_theme = "sphinx_rtd_theme"
htmlhelp_basename = "dotnetexampledoc"
extensions = ["autoapi.extension", "sphinxcontrib.dotnetdomain"]

autoapi_type = "dotnet"
# Turn this on for debugging
# autoapi_keep_files = True

autoapi_dirs = ["example/Identity/src/"]

import os

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
DIR = os.path.join(SITE_ROOT, autoapi_dirs[0])
if not os.path.exists(DIR):
    os.system(
        "git clone https://github.com/aspnet/Identity %s"
        % os.path.join(SITE_ROOT, "example/Identity")
    )
