import logging
import json

import uritemplate
from elasticsearch import Elasticsearch

from sheer.decorators import memoized


class QueryResults(object):

    def __init__(self, response_dict):
        self.response_dict = response_dict


class Query(object):

    def __init__(self, filename, site, es_index='content'):
        self.es_index = es_index
        self.es = Elasticsearch()
        self.filename = filename
        self.site=site
        self.__results = None

    def search(self, **kwargs):
        query_dict = json.loads(file(self.filename).read())
        query_dict['index'] = self.es_index
        query_dict.update(kwargs)
        if 'fields' not in query_dict:
            query_dict['fields'] = '*'
        if 'sort' not in query_dict:
            query_dict['sort'] = "date:desc"
        response = self.es.search(**query_dict)
        self.facets = []
        if response:
            self.__results = response
            if 'facets' in response:
                self.facets = response['facets']['tags']['terms']
        return {'results': list(self.iterate_results()), 'facets': self.facets}

    @property
    def results(self):
        if self.__results:
            return self.__results
        else:
            self.search()
            return self.__results

    def iterate_results(self):

        if 'hits' in self.results:
            for hit in self.results['hits']['hits']:
                hit.update(hit['fields'])
                del hit['fields']
                if hit['_type'] in self.site.permalink_map:
                    permalink_template = self.site.permalink_map[hit['_type']]
                    hit['permalink'] = uritemplate.expand(permalink_template, hit)
                yield hit


class QueryFinder(object):

    def __init__(self, searchpath, request, site):
        self.searchpath = searchpath
        self.site = site
        self.es_index = request.environ['ELASTICSEARCH_INDEX']

    @memoized
    def __getattr__(self, name):

        query_filename = name + ".json"
        found_file = self.searchpath.find(query_filename)
        if found_file:
            query = Query(found_file, self.site, self.es_index)
            return query
