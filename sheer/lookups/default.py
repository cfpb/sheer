from elasticsearch import Elasticsearch


def do_url(lookup_args, url_args):
    es = Elasticsearch()
    doc_type = lookup_args['type'] 
    id = url_args['id']
    document = es.get(index="content", doc_type=doc_type, id=id)['_source']
    return {"report": document}
