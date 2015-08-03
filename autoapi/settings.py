"""
Basic settings for AutoAPI projects.

You shouldn't need to touch this.
"""

import os

from .mappers import DotNetSphinxMapper, PythonSphinxMapper, GoSphinxMapper, JavaScriptSphinxMapper

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(SITE_ROOT, 'templates')

default_file_mapping = {
    'python': ['*.py'],
    'dotnet': ['project.json', '*.csproj', '*.vbproj'],
    'go': ['*.go'],
    'javascript': ['*.js'],
}

default_ignore_patterns = {
    'dotnet': ['*toc.yml', '*index.yml'],
    'python': ['*migrations*'],
}

default_backend_mapping = {
    'python': PythonSphinxMapper,
    'dotnet': DotNetSphinxMapper,
    'go': GoSphinxMapper,
    'javascript': JavaScriptSphinxMapper,
}
