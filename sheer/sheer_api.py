import json
import re

from paste.request import parse_formvars
from webob import Request, Response

from sheer.query import Query

class SheerAPI(object):
        
    def __init__(self, path):
        self.site_root = path


    def handle_wsgi(self, environ, start_response):
        start_response('200 OK', [('content-type', 'application/json')])
        query = Query(self.query_path(environ['PATH_INFO']), environ['ELASTICSEARCH_INDEX'])
        results = query.search(q='date:[2013-07-04 TO 2013-08-01]', sort='date:asc')
        data = []
        for rez in results:
            data.append( rez )
        return [ json.dumps( data ) ]


    def query_path(self, path_info):
        path_info = re.sub('^\/v\d+\/', '', path_info)
        return self.site_root + '/_queries/' + path_info + '.json'
