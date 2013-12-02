import json
import re

from paste.request import parse_formvars
from webob import Request, Response

from sheer.query import Query

class SheerAPI(object):

    def __init__(self, path):
        self.site_root = path


    def handle_wsgi(self, environ, start_response):
        args = self.process_arguments(environ)
        # get results
        query = Query(self.query_path(environ['PATH_INFO']), environ['ELASTICSEARCH_INDEX'])
        #q='date:[2013-02-04 TO 2013-08-01]',
        #sort='date:asc',
        #fields='title,text',
        #from_=1,
        #size=3,
        results = query.search( **args )
        data = []
        for rez in results:
            data.append(rez)
        # send back response
        start_response('200 OK', [('content-type', 'application/json')])
        return json.dumps(data)


    def process_arguments(self, environ):
        # check that arg name is allowed
        # check that arg value is allowed
        # process path args too, ie /v1/events/:event_id
        #  how to add to q, not overwrite it?
        fields = parse_formvars(environ)
        args = {}
        for item in fields.items():
            if item[0] == 'from':
                args['from_'] = item[1]
            else:
                args[item[0]] = item[1]
        args['q'] = "_id:testimony-before-senate-committee-on-banking-housing-and-urban-affairs.md"
        return args


    def query_path(self, path_info):
        path_info = re.sub('^\/v\d+\/', '', path_info)
        return self.site_root + '/_queries/' + path_info + '.json'
