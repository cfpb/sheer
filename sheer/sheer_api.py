import json
import re

from paste.request import parse_formvars
from webob import Request, Response

from sheer.query import Query

class SheerAPI(object):

    def __init__(self, path):
        self.site_root = path
        self.allowed_content = ['events', 'activity', 'reports']


    def handle_wsgi(self, environ, start_response):
        environ['ELASTICSEARCH_INDEX'] = None
        data = self.process_arguments(environ)
        # get results
        query = Query(self.site_root + '/_queries/' + data['content_type'] + '.json', environ['ELASTICSEARCH_INDEX'])
        results = query.search( **data['args'] )
        data = []
        for rez in results:
            data.append(rez)
        # send back response
        start_response('200 OK', [('content-type', 'application/json')])
        return json.dumps(data)


    def process_arguments(self, environ):
        # how to add to q, not overwrite it?
        # have allowed per content_type arguments
        fields = parse_formvars(environ)
        args = {}
        data = {}
        for item in fields.items():
            if item[0] == 'from':
                args['from_'] = item[1]
            else:
                args[item[0]] = item[1]

        pattern = r'^/(?P<api_version>v\d+)/(?P<content_type>' + '|'.join(self.allowed_content) + ')/?(?P<content_id>[^\/]+)?/?(?P<remainder>.+)?$'
        match = re.match(pattern, environ['PATH_INFO'])

        groups = match.groupdict()
        data['api_version'] = groups.get('api_version', '')
        data['content_type'] = groups.get('content_type', '')
        if groups['content_id']:
            args['q'] = '_id:' + groups['content_id']
        data['args'] = args
        return data
