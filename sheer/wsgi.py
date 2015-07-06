import os
import os.path
import re
import functools
import codecs
import markdown
import datetime
from urlparse import urlparse

import flask
import elasticsearch

from jinja2.loaders import FileSystemLoader
from werkzeug.routing import RequestRedirect
from .apis import add_apis_to_sheer
from .templates import date_formatter
from .views import handle_request, serve_error_page
from .utility import build_search_path, add_site_libs, build_search_path_for_request, find_in_search_path
from .query import QueryFinder, add_query_utilities
from .filters import add_filter_utilities
from .feeds import add_feeds_to_sheer
from .indexer import read_json_file

IGNORE_PATH_RE = [r'^[._].+', r'(_includes|_layouts)($|/)']
IGNORE_PATH_RE_COMPILED = [re.compile(pattern, flags=re.M)
                           for pattern in IGNORE_PATH_RE]


class Sheer(flask.Flask):

    def __init__(self,  *args, **kwargs):

        self.root_dir = kwargs['sheer_root']
        self.es = elasticsearch.Elasticsearch(kwargs['elasticsearch_servers'])
        self.es_index = kwargs['es_index']

        del kwargs['sheer_root']
        del kwargs['elasticsearch_servers']
        del kwargs['es_index']

        super(Sheer, self).__init__(*args, **kwargs)

    @property
    def jinja_loader(self, *args, **kwargs):
        request = flask.request
        search_path = build_search_path(self.root_dir,
                                        request.path,
                                        append=['_layouts', '_includes'],
                                        include_start_directory=True)

        return FileSystemLoader(search_path)

    def dispatch_request(self):
        try:
            flask_response = super(Sheer, self).dispatch_request()
            return flask_response

        except RequestRedirect:

            root_dir = flask.current_app.root_dir
            request_path = flask.request.path
            filesystem_path = flask.safe_join(root_dir, request_path[1:])
            if os.path.isfile(filesystem_path):
                return handle_request()
            raise


def should_ignore_this_path(pathname):

    for regex in IGNORE_PATH_RE_COMPILED:
        if regex.search(pathname):
            return True


def app_with_config(config):
    root_dir = config['location']
    elasticsearch_servers = config['elasticsearch']
    es_index = config['index']

    add_site_libs(root_dir)
    app = Sheer(__name__, static_folder=os.path.join(root_dir, 'static'),
                sheer_root=root_dir,
                elasticsearch_servers=elasticsearch_servers,
                es_index=es_index)

    if config.get('debug'):
        app.debug = True

    # Load blueprints
    blueprints_path = os.path.join(root_dir, '_settings/blueprints.json')
    if os.path.exists(blueprints_path):
        blueprints = read_json_file(blueprints_path)
        for key, value in blueprints.iteritems():
            package = value['package']
            module = value['module']

            # Using a less elegant way of doing dynamic imports to support 2.6
            try:
                blueprint = __import__(package, fromlist=[module])
            except ImportError:
                print "Error importing package {0}".format(key)
                continue
            app.register_blueprint(getattr(blueprint, module))

    # add lookup URL's
    permalinks_by_type = {}
    lookups_json_path = os.path.join(app.root_dir, '_settings/lookups.json')
    if os.path.exists(lookups_json_path):
        lookup_configs = read_json_file(lookups_json_path)
        for name, configuration in lookup_configs.items():
            app.add_url_rule(configuration['url'], name, functools.partial(
                handle_request, name, configuration))

            if u'type' in configuration and configuration.get("permalink") == True:
                content_type = configuration[u'type']
                permalinks_by_type[content_type] = name

    app.permalinks_by_type = permalinks_by_type

    @app.context_processor
    def add_queryfinder():
        search_path = build_search_path(app.root_dir,
                                        flask.request.path,
                                        append='_queries')
        context = {'queries': QueryFinder()}
        return context

    @app.context_processor
    def current_date():
        context = {'current_date': datetime.datetime.now()}
        return context

    @app.template_filter(name='possibles_to_list')
    def possibles_to_list(possibles):
        """
        This converts the output of 'possible_values_for' to a list, making it
        possible to check if an item is in an aggregation, from within the
        template.
        """
        return [item['key'] for item in possibles]

    @app.template_filter(name='domain_name')
    def domain_name(url):
        """
        This converts a full URL to the domain name, to be used when
        checking to see if a URL is in our list of vetted domains.
        """
        return urlparse(url).netloc.replace('www.', '')

    @app.template_filter(name='date')
    def date_filter(value, format="%Y-%m-%d", tz="America/New_York"):
        return date_formatter(value, format, tz)

    @app.template_filter(name='markdown')
    def markdown_filter(raw_text):
        return markdown.markdown(raw_text)

    @app.errorhandler(404)
    def no_lookup(e):
        return handle_request(None, None)

    @app.errorhandler(500)
    def general_error(e):
        return serve_error_page(500)

    add_query_utilities(app)
    add_apis_to_sheer(app)
    add_feeds_to_sheer(app)
    add_filter_utilities(app)

    return app
