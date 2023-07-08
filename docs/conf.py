# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import re

from sphinx import addnodes
from sphinx.util.docfields import TypedField

import autoapi

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Sphinx AutoAPI'
copyright = '2023, Read the Docs'
author = 'Read the Docs'
version = ".".join(str(x) for x in autoapi.__version_info__[:2])
release = autoapi.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'autoapi.extension',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx_design',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'changes/*.rst']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
html_css_files = ['overrides.css']

# -- Options for AutoAPI extension -------------------------------------------
autoapi_dirs = ['../autoapi']
autoapi_generate_api_docs = False

# -- Options for intersphinx extension ---------------------------------------

intersphinx_mapping = {
    'jinja': ('https://jinja.palletsprojects.com/en/3.0.x/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
    'python': ('https://docs.python.org/3/', None),
}

# -- Enable confval and event roles ------------------------------------------

event_sig_re = re.compile(r'([a-zA-Z-]+)\s*\((.*)\)')

def parse_event(env, sig, signode):
    m = event_sig_re.match(sig)
    if not m:
        signode += addnodes.desc_name(sig, sig)
        return sig
    name, args = m.groups()
    signode += addnodes.desc_name(name, name)
    plist = addnodes.desc_parameterlist()
    for arg in args.split(','):
        arg = arg.strip()
        plist += addnodes.desc_parameter(arg, arg)
    signode += plist
    return name


def setup(app):
    app.add_object_type('confval', 'confval',
                        objname='configuration value',
                        indextemplate='pair: %s; configuration value')
    fdesc = TypedField('parameter', label='Parameters',
                         names=('param',), typenames=('type',), can_collapse=True)
    app.add_object_type('event', 'event', 'pair: %s; event', parse_event,
                        doc_field_types=[fdesc])
