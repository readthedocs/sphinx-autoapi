"""
Basic settings for AutoAPI projects.

You shouldn't need to touch this.
"""

import os

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
