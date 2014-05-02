from elasticsearch import Elasticsearch
from sheer.query import QueryHit

def do_url(lookup_args, url_args):
    es = Elasticsearch()
    lookup_name = url_args['name']
    doc_type = lookup_args['type'] 
    id = url_args['id']
    document = es.get(index="content", doc_type=doc_type, id=id)
    hit = QueryHit(document)
    return {lookup_name: hit}
