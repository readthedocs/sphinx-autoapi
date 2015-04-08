import os

from jinja2 import Environment, FileSystemLoader

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

TEMPLATE_DIR = os.path.join(SITE_ROOT, 'templates')

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
