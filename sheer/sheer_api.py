import json
import re
import os.path

from paste.request import parse_formvars
from webob import Request, Response

from sheer.query import Query

class SheerAPI(object):

    def __init__(self, path, permalink_map):
        self.site_root = path
        self.start_response = None
        self.api_version = None
        self.allowed_content = ['events', 'activity', 'reports', 'search']
        self.content_type = None
        self.content_id = None
        # is a list, element 0 is a of the form '500 Internal Server Error',
        #       element 1 is data/message, ie {'Error':'Error message goes here'}
        #       ['500 Internal Server Error', {'Error':'This is the error message'}]
        self.errors = None
        self.args = {}
        self.results = []
        self.permalink_map = permalink_map


    def handle_wsgi(self, environ, start_response):
        environ['ELASTICSEARCH_INDEX'] = None
        self.start_response = start_response

        return self.process_arguments(environ, parse_formvars(environ)).calculate_results(environ).return_results()


    def check_errors(self):
        return self.errors != None


    def return_results(self):
        if self.check_errors():
            self.start_response(self.errors[0], [('content-type', 'application/json')])
            return json.dumps(self.errors[1])
        self.start_response('203 OK', [('content-type', 'application/json')])
        return json.dumps(self.results)


    def calculate_results(self, environ):
        if self.check_errors():
            return self

        query_file = self.site_root + '/_queries/' + self.content_type + '.json'
        if not os.path.isfile(query_file):
            self.errors = ['501 Not Implemented', {'Error':'Sheer API handling of %s is not implemented' % self.content_type}]
            return self

        try:
            query = Query(query_file, self, environ['ELASTICSEARCH_INDEX'])
            self.results = query.search( **self.args )
        except Exception as e:
            self.errors = ['500 Internal Server Error', {'Error':'%s' % e}]
        return self


    def add_2q(self, prepend, item):
        if item[0] == 'keyword':
            return '%s %s:(%s)' % (prepend, '_all', item[1].replace(',', ' '))
        if item[1].find(',') == -1:
            return "%s %s:\"%s\"" % (prepend, item[0], item[1])
        else:
            parts = item[1].split(',')
            join_by = '" AND ' + item[0] + ':"'
            return "%s %s:\"%s\"" % (prepend, item[0], join_by.join( parts ))


    def process_arguments(self, environ, fields):
        q_args = ['tags', 'text', 'title', 'type', 'keyword']
        for item in fields.items():
            if item[0] in q_args:
                if item[0] == 'type':
                    item = ('_type', item[1])
                if 'q' not in self.args:
                    self.args['q'] = self.add_2q('', item)
                else:
                    self.args['q'] += self.add_2q(' AND ', item)
            elif item[0] == 'from':
                self.args['from_'] = item[1]
            else:
                self.args[item[0]] = item[1]

        pattern = r'^/(?P<api_version>v\d+)/(?P<content_type>' \
                + '|'.join(self.allowed_content) + ')/?'
        match = re.match(pattern, environ['PATH_INFO'])
        if not match:
            self.errors = ['501 Not Implemented', {'Error':'Unknown API path'}]
            return self

        groups = match.groupdict()
        self.api_version = groups.get('api_version', '')
        self.content_type = groups.get('content_type', '')

        return self
