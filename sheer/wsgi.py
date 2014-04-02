import os
import os.path
import re
import functools

from jinja2.loaders import FileSystemLoader
from .lookups import add_lookups_to_sheer
from .apis import add_apis_to_sheer

import flask

from .templates import date_formatter

from .views import handle_request
from .utility import build_search_path
from .query import QueryFinder

IGNORE_PATH_RE = ['static', r'^[._].+', r'(_includes|_layouts)($|/)']
IGNORE_PATH_RE_COMPILED = [re.compile(pattern, flags=re.M) for pattern in IGNORE_PATH_RE]


class Sheer(flask.Flask):

    def __init__(self,  *args, **kwargs):
        if 'sheer_root' in kwargs:
            self.root_dir = kwargs.get('sheer_root')
            del kwargs['sheer_root']
        
        super(Sheer, self).__init__(*args, **kwargs)

    @property
    def jinja_loader(self,*args, **kwargs):
        request = flask.request
        search_path = build_search_path(self.root_dir,
                                        request.path,
                                        append='_layouts',
                                        include_start_directory=True)

        print "\a"
        return FileSystemLoader(search_path)


def should_ignore_this_path(pathname):

    for regex in IGNORE_PATH_RE_COMPILED:
        if regex.search(pathname):
            return True


def app_with_config(root_dir):
    app = Sheer(__name__, static_folder=os.path.join(root_dir, 'static'),
                sheer_root=root_dir)

    for here, dirs, files in os.walk(root_dir):
        relpath = os.path.relpath(here, root_dir)
        if relpath == '.':
            relurl = '/'
        else:
            relurl = '/' + relpath + '/'

        if should_ignore_this_path(relpath):
            continue

        # "seeker" is for lookup files, "index" serves directory roots

        seeker_handler = functools.partial(handle_request, diskpath=here)
        index_handler = functools.partial(handle_request, diskpath=here, remainder=None)

        seeker_url = relurl + '<remainder>'
        index_url = relurl

        seeker_view_name = relurl.replace('/','_')
        index_view_name = seeker_view_name + '_index'

        app.add_url_rule(seeker_url,seeker_view_name, seeker_handler)
        app.add_url_rule(index_url,index_view_name, index_handler)
    
    @app.context_processor
    def add_queryfinder():
        search_path = build_search_path(app.root_dir,
                                        flask.request.path,
                                        append='_queries')
        context = {'queries' : QueryFinder(search_path, flask.request)}
        return context
        
    @app.template_filter(name='date')
    def date_filter(value, format="%Y-%m-%d"):
        return date_formatter(value,format)
        
    add_lookups_to_sheer(app)
    add_apis_to_sheer(app)
    return app
