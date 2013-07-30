import logging
import json
import requests

from sheer.decorators import memoized


class QueryResults(object):

    def __init__(self, response_dict):
        self.response_dict = response_dict


class Query(object):

    def __init__(self, filename, es_index):
        self.endpoint = es_index + '_search'
        self.filename = filename
        self.__results = None

    def search(self):
        query_dict = json.loads(file(self.filename).read())
        search_txt = json.dumps(query_dict)
        logging.debug(search_txt)
        response = requests.post(self.endpoint, search_txt)
        if response.status_code == 200:
            self.__results = json.loads(response.text)
        else:
            logging.debug(response.text)
            return
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
