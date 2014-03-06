import os
import codecs
import logging
import json

import uritemplate
from elasticsearch import Elasticsearch
import dateutil.parser

from time import mktime, strptime
from datetime import datetime

from sheer.decorators import memoized


class QueryResults(object):

    def __init__(self, response_dict):
        self.response_dict = response_dict


class Query(object):
    #TODO: This no longer respects the elasticsearch URL passed in on the CLI

    def __init__(self, filename, site, es_index='content', json_safe=False):
        self.es_index = es_index
        self.es = Elasticsearch()
        self.filename = filename
        self.site = site
        self.__results = None
        self.json_safe = json_safe
        self.read_default_mappings()

    def search(self, **kwargs):
        query_dict = json.loads(file(self.filename).read())
        query_dict['index'] = self.es_index
        query_dict.update(kwargs)
        if 'fields' not in query_dict:
            query_dict['fields'] = '*'
        if 'sort' not in query_dict:
            query_dict['sort'] = "date:desc"
        response = self.es.search(**query_dict)
        self.facets = {}
        if response:
            self.__results = response
            if 'facets' in response:
                for facet in response['facets']:
                    self.facets[facet] = response['facets'][facet]['terms']
        return {'results': list(self.iterate_results()), 'facets': self.facets}

    @property
    def results(self):
        if self.__results:
            return self.__results
        else:
            self.search()
            return self.__results

    def read_default_mappings(self):
        #TODO not sure this needs to exist

        default_mapping_path = '_defaults/mappings.json'
        # Load default mapping (or not)
        if os.path.exists(default_mapping_path):
            try:
                with codecs.open(default_mapping_path, 'r', 'utf-8') as json_file:
                    default_mapping = json.loads(json_file.read())
                    self.default_mapping = default_mapping['properties']
            except ValueError:
                sys.exit("default mapping present, but is not valid JSON")
        else:
            self.default_mapping = {}

    def convert_datatypes(self, hit):

        if self.json_safe:
            return

        if 'fields' not in hit:
            return
        for field in hit['fields']:
            if field in self.default_mapping and self.default_mapping[field]['type'] == 'date':
                time_obj = dateutil.parser.parse(hit['fields'][field])
                hit['fields'][field] = time_obj

    def iterate_results(self):
        if 'hits' in self.results:
            for hit in self.results['hits']['hits']:
                self.convert_datatypes(hit)
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
