import sys
import click
import os
import glob

from flask import Flask, Markup, Response, render_template, render_template_string, send_from_directory, current_app, safe_join
from flask_flatpages import FlatPages, pygmented_markdown, pygments_style_defs
from flask_frozen import Freezer

app = Flask(__name__)
app.config.from_object('settings')

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

@app.route('/articles/<slug>/<path:filename>')
def article_static(slug, filename):
    article = get_pages_by_slug(slug)
    directory = os.path.dirname(safe_join(current_app.root_path, current_app.config.get("FLATPAGES_ROOT"), article.path))
    return send_from_directory(directory, filename)

@app.route('/tag/<tag>/')
def tag(tag):
    articles = get_pages_by_tags(tag)
    article = ''
    return render_template('tag.html', **locals())
    
@app.route('/sitemap.xml')
def sitemap():
    server_name = current_app.config.get("SITEMAP_SERVER_NAME")
    articles = get_pages_sorted()
    index = get_pages_by_slug('index')
    tags = set()
    for article in articles:
        for tag in article.meta.get("tags",[]):
            tags.add(tag)
    return Response(render_template('sitemap.xml', **locals()), mimetype='application/xml')
    
@app.route('/robots.txt')
def robots():
    server_name = current_app.config.get("SITEMAP_SERVER_NAME")
    return Response(render_template('robots.txt', **locals()), mimetype='text/plain')
    
@app.route('/google0e9a29b6ad0a512a.html')
def google_verification():
    return render_template('google0e9a29b6ad0a512a.html')

@freezer.register_generator
def other_static_files():
    """
    Register the URLs for the robots and sitemap routes to frozen flask
    """
    yield 'robots', {}
    yield 'sitemap', {}
    yield 'google_verification', {}
    
@freezer.register_generator
def article_static_files():
    """
    Register the URLS for article's static files (PNG images only for now) to
    frozen flask.
    """
    for p in pages:
        directory = os.path.dirname(safe_join(current_app.root_path, current_app.config.get("FLATPAGES_ROOT"), p.path))
        for static_file in glob.glob(os.path.join(directory, "*.png")):
            yield 'article_static', {'slug':p.meta.get('slug'), 'filename':os.path.basename(static_file)}

@app.cli.command()
def freeze():
    print("Freezing...")
    freezer.freeze()
