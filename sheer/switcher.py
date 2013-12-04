""" Simple class to forward control to SheerAPI or Site, depending on request path """
import re

from sheer_api import SheerAPI
from site import Site

class Switcher(object):

    def __init__(self, path):
        self.site_root = path

    def handle_wsgi(self, environ, start_response):
        if re.match(r'^/v\d+/', environ['PATH_INFO']):
            sheer_api = SheerAPI(self.site_root)
            return sheer_api.handle_wsgi(environ, start_response)

        site = Site(self.site_root)
        return site.handle_wsgi(environ, start_response)


