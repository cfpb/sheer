import os
import codecs
import logging
import json

import flask

from elasticsearch import Elasticsearch
import dateutil.parser

from time import mktime, strptime
import datetime

from sheer.decorators import memoized
from sheer.utility import find_in_search_path


ALLOWED_SEARCH_PARAMS = ('doc_type',
        'analyze_wildcard', 'analyzer', 'default_operator', 'df',
        'explain', 'fields', 'indices_boost', 'lenient',
        'allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'lowercase_expanded_terms', 'from_', 'preference', 'q', 'routing',
        'scroll', 'search_type', 'size', 'sort', 'source', 'stats',
        'suggest_field', 'suggest_mode', 'suggest_size', 'suggest_text', 'timeout',
        'version')

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
              'date': dateutil.parser.parse,
              'long':float}

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
        app = flask.current_app
        rule = app.permalinks_by_type.get(self.type)
        if rule:
            build_with=dict(id = self.hit_dict['_id'])
            _ , url = rule.build(build_with)
            return url

    def __getattr__(self, attrname):
        value = field_or_source_value(attrname, self.hit_dict)
        datatype = datatype_for_fieldname_in_mapping(attrname, self.type, self.mapping)
        return coerced_value(value, datatype)

    def json_compatible(self):
        hit_dict = self.hit_dict
        fields =  hit_dict.get('fields') or hit_dict.get('_source', {}).keys()
        return {field: getattr(self, field) for field in fields}

class QueryResults(object):

    def __init__(self, result_dict):
        self.result_dict = result_dict
        self.total = int(result_dict['hits']['total'])
        self.size = int(result_dict['query'].get('size', '10'))
        self.from_ = int(result_dict['query'].get('from', 1))
        self.pages = self.total / self.size + int(self.total%self.size > 0)

    def __iter__(self):
        if 'hits' in self.result_dict and 'hits' in self.result_dict['hits']:
            for hit in self.result_dict['hits']['hits']:
                yield QueryHit(hit)

    def json_compatible(self):
        response_data = {}
        response_data['total'] = self.result_dict['hits']['total']
        if self.size:
            response_data['size'] = self.size

        if self.from_:
            response_data['from'] = self.from_
        
        if self.pages:
            response_data['pages'] = self.pages
        response_data['results'] = [hit.json_compatible() for hit in self.__iter__()]
        return response_data


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
        if 'facet' in kwargs:
            kwargs
        query_dict.update(kwargs)

        if 'sort' not in query_dict:
            query_dict['sort'] = "date:desc"
        response = self.es.search(**query_dict)

        response['query']= query_dict
        return QueryResults(response)

    def search_with_url_arguments(self, **kwargs):
        # TODO: DRY with above
        query_dict = json.loads(file(self.filename).read())
        query_dict['index'] = self.es_index
        query_dict.update(kwargs)

        if 'sort' not in query_dict:
            query_dict['sort'] = "date:desc"
        
        request = flask.request
        args_flat = request.args.to_dict(flat=True)


        if 'page' in args_flat:
            args_flat['from_'] = int(query_dict.get('size', '10')) * (int(args_flat['page'])-1)

        query_dict.update(args_flat)
        final_query_dict = {k:v for k,v in query_dict.items() if k in ALLOWED_SEARCH_PARAMS}
        response = self.es.search(**final_query_dict)
        response['query']= query_dict
        return QueryResults(response)

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

    def __init__(self, searchpath = None):
        if searchpath:
            self.searchpath = searchpath
        else:
            self.searchpath = [os.path.join(flask.current_app.root_dir, '_queries')]
        self.es_index = flask.request.environ.get('ELASTICSEARCH_INDEX', 'content')
        # TODO must respect global config!

    def __getattr__(self, name):
        query_filename = name + ".json"
        found_file = find_in_search_path(query_filename, self.searchpath)

        if found_file is not None:
            query = Query(found_file, self.es_index)
            return query

class QueryJsonEncoder(json.JSONEncoder):
    query_classes = [QueryResults, QueryHit]
    def default(self, obj):
        if type(obj) in (datetime.datetime, datetime.date):
            return obj.isoformat()
        if type(obj) in self.query_classes:
            return obj.json_compatible() 

        return json.JSONEncoder.default(self, obj)
