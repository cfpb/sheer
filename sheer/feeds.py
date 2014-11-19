from urlparse import urljoin
from flask import request
from werkzeug.contrib.atom import AtomFeed
import flask
import os

from .query import QueryFinder
from .indexer import read_json_file

PARAM_TOKEN = '$$'
ALLOWED_FEED_PARAMS = ('feed_title')
ALLOWED_ENTRY_PARAMS = ('entry_url', 'entry_title', 'entry_content',
                        'entry_author', 'entry_updated', 'entry_content_type',
                        'entry_summary', 'entry_published', 'entry_rights')


def make_external(url):
    return urljoin(request.url_root, url)


def get_feed_settings(name):
    app = flask.current_app
    queries_dir = os.path.join(app.root_dir, '_queries')
    query_path = os.path.join(queries_dir, '{0}.json'.format(name))
    if os.path.exists(query_path):
        query_file = read_json_file(query_path)
        return query_file.get('feed')


class Feed(object):

    # Make sure only allowed feed params are passed into the feed
    def __init__(self, settings):
        self.feed_url = request.url
        self.url = request.url_root
        for setting in settings:
            if setting.startswith('feed_') and setting in ALLOWED_FEED_PARAMS:
                setting_trimmed = setting.replace('feed_', '')
                setattr(self, setting_trimmed, settings[setting])


class Entry(object):

    # Make sure only allowed entry params are passed into the feed
    def __init__(self, item, settings):
        for setting in settings:
            attribute = settings[setting].replace('$$', '')
            if setting.startswith('entry_') and \
                setting in ALLOWED_ENTRY_PARAMS and \
                    hasattr(item, attribute):
                setting_trimmed = setting.replace('entry_', '')
                setattr(self, setting_trimmed, getattr(item, attribute))

        if self.url:
            self.url = make_external(self.url)


def add_feeds_to_sheer(app):

    @app.route('/feed/<name>/')
    def recent_feed(name):
        settings = get_feed_settings(name) or flask.abort(404)
        feed = Feed(settings)
        atom_feed = AtomFeed(**feed.__dict__)
        query_finder = QueryFinder()
        query = getattr(query_finder, name) or flask.abort(404)
        items = query.search_with_url_arguments()

        for item in items:
            entry = Entry(item, settings)
            atom_feed.add(**entry.__dict__)
        return atom_feed.get_response()
