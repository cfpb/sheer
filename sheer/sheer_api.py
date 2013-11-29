import json
import re
from paste.request import parse_formvars
from webob import Request, Response

from sheer.query import Query

def handle_wsgi(environ, start_response):
    start_response('200 OK', [('content-type', 'application/json')])
    results = Query(query_path(environ['PATH_INFO']), environ['ELASTICSEARCH_INDEX']).search()
    data = []
    for rez in results:
        data.append( rez )
    return [ json.dumps( data ) ]


def query_path( path_info ):
    base_path = '/Users/gorobets/projects/sheer-flapjack-demos/_queries/'
    path_info = re.sub('^\/v\d+\/', '', path_info)
    return base_path + path_info + '.json'
