from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

import flask

from sheer.query import QueryHit

def do_url(lookup_args, url_args):
    es = Elasticsearch()
    lookup_name = url_args['name']
    doc_type = lookup_args['type'] 
    id = url_args['id']
    try: 
        document = es.get(index="content", doc_type=doc_type, id=id)
    except NotFoundError:
        flask.abort(404)
    hit = QueryHit(document)
    return {lookup_name: hit}
