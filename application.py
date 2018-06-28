import sys
import click

from flask import Flask, Markup, render_template, render_template_string
from flask_flatpages import FlatPages, pygmented_markdown, pygments_style_defs
from flask_frozen import Freezer

DEBUG = True

def prerender_jinja(text):
    prerendered_body = render_template_string(Markup(text))
    return pygmented_markdown(prerendered_body)

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['FLATPAGES_AUTO_RELOAD'] = True
app.config['FLATPAGES_HTML_RENDERER'] = prerender_jinja
app.config['FLATPAGES_ROOT'] = 'content'
app.config['FLATPAGES_EXTENSION'] = '.md'
app.config['FLATPAGES_MARKDOWN_EXTENSIONS'] = ['codehilite']

#app.config['FREEZER_DESTINATION'] = 'build'
#app.config['FREEZER_SKIP_EXISTING'] = True
app.config['FREEZER_RELATIVE_URLS'] = True


pages = FlatPages(app)
freezer = Freezer(app=app, log_url_for=True, with_static_files=True)

def get_pages(**kwargs):
    """
    Convenience function to get one or more pages by one or more of its 
    metadata items.
    """
    pass

def get_pages_by_slug(slug):
    for p in pages:
        if p.meta.get('slug', None) == slug:
            return p 
            
def get_pages_by_tags(*args):
    tag_set = set(args)
    pages_ = (p for p in pages if tag_set & set(p.meta.get('tags','')))
    return sorted(pages_, reverse=True, key=lambda p: p.meta['date'])

def get_pages_sorted(sort_by='date', reverse=True, page_type='article'):
    pages_ = (p for p in pages if p.meta.get('status','') == 'published' and p.meta.get('type','') == page_type)
    return sorted(pages_, reverse=reverse, key=lambda p: p.meta[sort_by])
    
def get_related_pages(page):
    """
    Get related pages by using overlapping tags.
    """
    pass

@app.route('/')
def index():
    index = get_pages_by_slug('index')
    articles = get_pages_sorted()
    return render_template('index.html', **locals())

@app.route('/articles/<slug>/')
def article(slug):
    article = get_pages_by_slug(slug)
    return render_template('article.html', **locals())

@app.route('/tag/<tag>/')
def tag(tag):
    articles = get_pages_by_tags(tag)
    article = ''
    return render_template('tag.html', **locals())
    
    
@app.cli.command()
def freeze():
    print("Freezing...")
    freezer.freeze()
#
#if __name__ == '__main__':
#    freezer.freeze()