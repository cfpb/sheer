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
from sheer.utility import find_in_search_path


@memoized
def mapping_for_type(typename):
    #TODO respect configured index
    es = Elasticsearch()
    return es.indices.get_mapping(index="content", doc_type= typename) 

def field_or_source_value(fieldname, hit_dict):
    if 'fields' in hit_dict and fieldname in hit_dict['fields']:
        return hit_dict['fields'][fieldname]

    if '_source' in hit_dict and fieldname in hit_dict['_source']:
        return hit_dict['_source'][fieldname]


def datatype_for_fieldname_in_mapping(fieldname, hit_type, mapping_dict):
    try:
        return mapping_dict["content"]["mappings"][hit_type]["properties"][fieldname]["type"]
    except KeyError:
        return 'string'

def coerced_value(value, datatype):
    TYPE_MAP={'string': unicode,
              'date': dateutil.parser.parse}

    coercer = TYPE_MAP[datatype]

    if type(value) == list:
        if len(value) > 0:
            coerced = coercer(value[0])
            return coerced
        else:
            return ""

    else:
        return coercer(value)

        

class QueryHit(object):
    def __init__(self, hit_dict):
        self.hit_dict = hit_dict
        self.type = hit_dict['_type']
        self.mapping = mapping_for_type(self.type)

    @property
    def permalink(self):
        return ""

    def __getattr__(self, attrname):
        value = field_or_source_value(attrname, self.hit_dict)
        datatype = datatype_for_fieldname_in_mapping(attrname, self.type, self.mapping)
        return coerced_value(value, datatype)


class QueryResults(object):

    def __init__(self, result_dict):
        self.result_dict = result_dict

    def __iter__(self):
        if 'hits' in self.result_dict and 'hits' in self.result_dict['hits']:
            for hit in self.result_dict['hits']['hits']:
                yield QueryHit(hit)

class Query(object):
    #TODO: This no longer respects the elasticsearch URL passed in on the CLI

    def __init__(self, filename=None, es_index='content', json_safe=False):
        # TODO: make the no filename case work

        self.es_index = es_index
        self.es = Elasticsearch()
        self.filename = filename
        self.__results = None
        self.json_safe = json_safe

    def search(self, **kwargs):
        query_dict = json.loads(file(self.filename).read())
        query_dict['index'] = self.es_index
        query_dict.update(kwargs)
        if 'sort' not in query_dict:
            query_dict['sort'] = "date:desc"
        response = self.es.search(**query_dict)

        return {'results': QueryResults(response)}

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
                self.convert_datatypes(hit)
                hit.update(hit['fields'])
                del hit['fields']
                yield hit


class QueryFinder(object):

    def __init__(self, searchpath, request):
        self.searchpath = searchpath
        self.es_index = request.environ.get('ELASTICSEARCH_INDEX', 'content')
        # TODO must respect global config!

    def __getattr__(self, name):
        query_filename = name + ".json"
        found_file = find_in_search_path(query_filename, self.searchpath)

        if found_file is not None:
            query = Query(found_file, self.es_index)
            return query
