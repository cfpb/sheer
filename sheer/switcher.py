""" Simple class to forward control to SheerAPI or Site, depending on request path """
import re
import os
import os.path
import codecs
import json

from sheer_api import SheerAPI
from site import Site

PERMALINKS_JSON_PATH = '_settings/permalinks.json'

class Switcher(object):

    def __init__(self, path):
        self.site_root = path

        if os.path.exists(PERMALINKS_JSON_PATH):
            permalinks_file = codecs.open(PERMALINKS_JSON_PATH, encoding='utf8')
            self.permalink_map = json.loads(permalinks_file.read())

        else:
            self.permalink_map = {}


    def handle_wsgi(self, environ, start_response):
        if re.match(r'^/v\d+/', environ['PATH_INFO']):
            sheer_api = SheerAPI(self.site_root, self.permalink_map)
            return sheer_api.handle_wsgi(environ, start_response)

        site = Site(self.site_root, self.permalink_map)
        return site.handle_wsgi(environ, start_response)


