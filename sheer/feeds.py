from urlparse import urljoin
from flask import request
from werkzeug.contrib.atom import AtomFeed
import flask

from .query import QueryFinder

def make_external(url):
    return urljoin(request.url_root, url)

def add_feeds_to_sheer(app):

    @app.route('/feed/<name>')
    def recent_feed(name):
        feed = AtomFeed('Consumer Financial Protection Bureau - {}'.format(name), 
                        feed_url=request.url, 
                        url=request.url_root)
        query_finder = QueryFinder()
        query = getattr(query_finder, name) or flask.abort(404)
        items = query.search_with_url_arguments()

        for item in items:
            feed.add(item.title, item.content,
                 content_type='html',
                 author=item.author,
                 url=make_external(item.permalink),
                 updated=item.date)       
        return feed.get_response()