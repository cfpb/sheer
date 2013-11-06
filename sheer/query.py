import logging
import json

from elasticsearch import Elasticsearch

from sheer.decorators import memoized


class QueryResults(object):

    def __init__(self, response_dict):
        self.response_dict = response_dict


class Query(object):

    def __init__(self, filename, es_index='content'):
        self.es_index = es_index
        self.es = Elasticsearch()
        self.filename = filename
        self.__results = None

    def search(self):
        query_dict = json.loads(file(self.filename).read())
        query_dict['index'] = self.es_index
        if 'fields' not in query_dict:
            query_dict['fields'] = '*'
        response = self.es.search(**query_dict)
        if response:
            self.__results = response
        return self.iterate_results()

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
                yield hit


class QueryFinder(object):

    def __init__(self, searchpath, request):
        self.searchpath = searchpath
        self.es_index = request.environ['ELASTICSEARCH_INDEX']

    @memoized
    def __getattr__(self, name):

        query_filename = name + ".json"
        found_file = self.searchpath.find(query_filename)
        if found_file:
            query = Query(found_file, self.es_index)
            return query
