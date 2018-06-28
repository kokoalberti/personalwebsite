# General settings
DEBUG = True

# Some hacks to allow using Jinja markup within the Markdown templates
from flask_flatpages import pygmented_markdown
from flask import Markup, render_template_string
def prerender_jinja(text):
    prerendered_body = render_template_string(Markup(text))
    return pygmented_markdown(prerendered_body)

# Settings for Flask-FlatPages
FLATPAGES_AUTO_RELOAD = True
FLATPAGES_HTML_RENDERER = prerender_jinja
FLATPAGES_ROOT = 'content'
FLATPAGES_EXTENSION = '.md'
FLATPAGES_MARKDOWN_EXTENSIONS = ['codehilite']

# Settings for Frozen-Flask
#FREEZER_DESTINATION = 'build'
#FREEZER_SKIP_EXISTING = True
#FREEZER_RELATIVE_URLS = True