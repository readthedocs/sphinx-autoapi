templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "pystdlib"
copyright = "2015, readthedocs"
author = "readthedocs"
version = "0.1"
release = "0.1"
language = "en"
exclude_patterns = ["_build"]
pygments_style = "sphinx"
todo_include_todos = False
html_theme = "alabaster"
htmlhelp_basename = "pystdlibdoc"
extensions = ["autoapi.extension"]
autoapi_dirs = ["stdlib"]
autoapi_file_pattern = "*.py"
autoapi_keep_files = True
autoapi_options = [
    "members",
    "undoc-members",
    "special-members",
    "imported-members",
    "inherited-members",
]
