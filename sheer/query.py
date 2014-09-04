import os
import codecs
import logging
import json

import flask

import dateutil.parser

from time import mktime, strptime
import datetime

from werkzeug.urls import url_encode
from werkzeug.datastructures import MultiDict

from sheer.decorators import memoized
from sheer.utility import find_in_search_path
from sheer.filters import filter_dsl_from_multidict


ALLOWED_SEARCH_PARAMS = ('doc_type',
        'analyze_wildcard', 'analyzer', 'default_operator', 'df',
        'explain', 'fields', 'indices_boost', 'lenient',
        'allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'lowercase_expanded_terms', 'from_', 'preference', 'q', 'routing',
        'scroll', 'search_type', 'size', 'sort', 'source', 'stats',
        'suggest_field', 'suggest_mode', 'suggest_size', 'suggest_text', 'timeout',
        'version')

def mapping_for_type(typename, es=None, es_index=None):
    if not es:
        es = flask.current_app.es
    if not es_index:
        es_index =flask.current_app.es_index

    return es.indices.get_mapping(index=es_index, doc_type= typename) 

def field_or_source_value(fieldname, hit_dict):
    if 'fields' in hit_dict and fieldname in hit_dict['fields']:
        return hit_dict['fields'][fieldname]

    if '_source' in hit_dict and fieldname in hit_dict['_source']:
        return hit_dict['_source'][fieldname]


def datatype_for_fieldname_in_mapping(fieldname, hit_type, mapping_dict):
    es = flask.current_app.es
    es_index =flask.current_app.es_index

    try:
        return mapping_dict[es_index]["mappings"][hit_type]["properties"][fieldname]["type"]
    except KeyError:
        return None

def coerced_value(value, datatype):
    if datatype == None or value == None:
        return value

    TYPE_MAP={'string': unicode,
              'date': dateutil.parser.parse,
              'dict': dict,
              'float':float,
              'long':float}

    coercer = TYPE_MAP[datatype]

    if type(value) == list:
        if value and type(value[0]) == list:
            return [[coercer(y) for y in v] for v in value]
        else:
            return [coercer(v) for v in value] or ""
    else:
        return coercer(value)

        

class QueryHit(object):
    def __init__(self, hit_dict, es=None, es_index=None):
        self.hit_dict = hit_dict
        self.type = hit_dict['_type']
        self.mapping = mapping_for_type(self.type, es=es, es_index=es_index )

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
        return dict((field, getattr(self, field)) for field in fields)

class QueryResults(object):

    def __init__(self, result_dict, pagenum = 1):
        self.result_dict = result_dict
        self.total = int(result_dict['hits']['total'])
        if 'query' in result_dict:
            self.size = int(result_dict['query'].get('size', '10'))
            self.from_ = int(result_dict['query'].get('from', 1))
            self.pages = self.total / self.size + int(self.total%self.size > 0)
        else:
            self.size, self.from_, self.pages = 10,1,1    

        self.current_page = pagenum

    def __iter__(self):
        if 'hits' in self.result_dict and 'hits' in self.result_dict['hits']:
            for hit in self.result_dict['hits']['hits']:
                yield QueryHit(hit)

    def facets(self, fieldname):
        if "facets" in self.result_dict and fieldname in self.result_dict["facets"]:
            return self.result_dict['facets'][fieldname]["terms"]


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

    def url_for_page(self, pagenum):
        current_args = flask.request.args
        args_dict = MultiDict(current_args)
        if pagenum != 1:
            args_dict['page'] = pagenum
        elif 'page' in args_dict:
            del args_dict['page']
            
        encoded = url_encode(args_dict)
        if encoded:
            url = "".join([flask.request.path, "?",url_encode(args_dict)])
            return url
        else:
            return flask.request.path


class Query(object):

    def __init__(self, filename=None, json_safe=False):
        # TODO: make the no filename case work

        app = flask.current_app
        self.es_index = app.es_index
        self.es = app.es
        self.filename = filename
        self.__results = None
        self.json_safe = json_safe

    def search_with_url_arguments(self, term_facets=None, **kwargs):
        query_file = json.loads(file(self.filename).read())
        query_dict = query_file['query']
        query_dict.update(kwargs)
        pagenum = 1
        
        request = flask.request
        url_filters = filter_dsl_from_multidict(request.args)
        args_flat = request.args.to_dict(flat=True)
        query_body = {}

        if term_facets:
            facets_dsl = {}
            if type(term_facets) is str:
                term_facets = [term_facets] # so we can treat it as a list
            for fieldname in term_facets:
                facets_dsl[fieldname]={"terms":{"field":fieldname, "size":10000}}
            query_body["facets"] = facets_dsl
        else:
            if 'page' in args_flat:
                args_flat['from_'] = int(query_dict.get('size', '10')) * (int(args_flat['page'])-1)
                pagenum = int(args_flat['page'])

            args_flat_filtered = dict([(k,v) for k,v in args_flat.items() if v])
            query_dict.update(args_flat_filtered)
            query_body['query'] = {'filtered':{'filter': {}}}
            if url_filters:
                query_body['query']['filtered']['filter']['and'] = [f for f in url_filters]

            if 'filters' in query_file:
                if 'and' not in query_body['query']['filtered']['filter']:
                    query_body['query']['filtered']['filter']['and'] = []
                for json_filter in query_file['filters']:
                    query_body['query']['filtered']['filter']['and'].append(json_filter)
        final_query_dict = dict((k, v) for (k, v) in query_dict.items() if k in ALLOWED_SEARCH_PARAMS)
        final_query_dict['index'] = self.es_index
        final_query_dict['body'] = query_body
        response = self.es.search(**final_query_dict)
        response['query']= query_dict
        return QueryResults(response,pagenum )

    def possible_values_for(self, field, **kwargs):
        results = self.search_with_url_arguments(term_facets=[field], **kwargs)
        return results.facets(field)
        

    @property
    def results(self):
        if self.__results:
            return self.__results
        else:
            self.search()
            return self.__results



    #TODO does this function still need to exist?
    def iterate_results(self):
        if 'hits' in self.results:
            for hit in self.results['hits']['hits']:
                self.convert_datatypes(hit)
                hit.update(hit['fields'])
                del hit['fields']
                yield hit


class QueryFinder(object):

    def __init__(self):
        app = flask.current_app
        self.es = app.es
        self.es_index = app.es_index
        self.queries_dir = os.path.join(app.root_dir,'_queries')

    def __getattr__(self, name):
        query_filename = name + ".json"
        query_file_path = os.path.join(self.queries_dir,query_filename)

        if os.path.exists(query_file_path):
            query = Query(query_file_path, self.es_index)
            return query

class QueryJsonEncoder(json.JSONEncoder):
    query_classes = [QueryResults, QueryHit]
    def default(self, obj):
        if type(obj) in (datetime.datetime, datetime.date):
            return obj.isoformat()
        if type(obj) in self.query_classes:
            return obj.json_compatible() 

        return json.JSONEncoder.default(self, obj)


def add_query_utilities(app):
    def more_like_this(hit, **kwargs):
        es = flask.current_app.es
        es_index = app.es_index
        doctype, docid = hit.type, hit._id
        raw_results = es.mlt(index=es_index, doc_type=doctype, id=docid, **kwargs)
        return QueryResults(raw_results)

    def get_document(doctype, docid):
        es = flask.current_app.es
        es_index = app.es_index
        raw_results = es.get(index=es_index, doc_type=doctype, id=docid)
        return QueryHit(raw_results)

    @app.context_processor
    def query_utility_context_processor():
        context = {'more_like_this': more_like_this,
                   'get_document': get_document}
        return context
