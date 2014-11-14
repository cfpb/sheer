import os.path
import codecs

import flask
from flask import request
from werkzeug.exceptions import HTTPException, NotFound

from .utility import build_search_path, build_search_path_for_request, find_in_search_path
from .query import QueryHit


def do_lookup(name, doc_type, **search_params):
    es = flask.current_app.es
    es_index = flask.current_app.es_index

    lookup_name = name
    doc_type = doc_type 
    id = search_params['id']

    try: 
        document = es.get(index=es_index, doc_type=doc_type, id=id)
    except NotFoundError:
        document = None

    hit = QueryHit(document)
    return {lookup_name: hit}

def handle_request(lookup_name=None, lookup_config=None, **kwargs):
    lookup_doc = None
    root_dir = flask.current_app.root_dir 
    request_path = request.path

    if request_path.endswith('/'):
            request_path += ('index.html')

    translated_path = os.path.join(root_dir, request_path[1:])

    if not request_path.endswith('.html') and os.path.exists(translated_path):
        flask.send_file(translated_path)

    if lookup_name:
        doc_type = lookup_config['type']
        search_params = lookup_config.copy()
        del search_params['url']
        del search_params['type']

        lookup_doc = do_lookup(lookup_name, doc_type, **kwargs)

    template_candidates = [translated_path]
    if lookup_doc:
        template_candidates += build_search_path(root_dir, request.path,append='_single.html', include_start_directory=False)

    try:

        template_path = next(t for t in template_candidates if os.path.exists(t))
        #import pdb;pdb.set_trace()
        if os.path.exists(template_path):
            template_context = {}
            template_context.update(lookup_doc or {})

            with codecs.open(template_path, encoding="utf-8") as template_source:
                return flask.render_template_string(template_source.read(),**template_context)

    except StopIteration:
        return serve_error_page(404)



def serve_error_page(error_code):
    request = flask.request
    # TODO: this seems silly 
    # We shouldn't even need to send the request object,
    # and the second argument should usually be request.path anyways
    search_path = build_search_path_for_request(request, request.path, append=['_layouts','_includes'], include_start_directory=True)
    template_path = find_in_search_path('%s.html' % error_code, search_path)

    if template_path:
        with codecs.open(template_path, encoding="utf-8") as template_source:
            return flask.render_template_string(template_source.read()), error_code
    else:
        return "Please provide a %s.html!" % error_code

# legacy view code, hopefully to be deleted
def serve_requested_file(directory, requested_file, lookup_results=None):
    complete_path = os.path.join(directory, requested_file)
    if os.path.exists(complete_path):
        if requested_file.lower().endswith('.html'):
            pass
        else:
            return flask.send_from_directory(directory, requested_file)
    elif lookup_results:
        lookup_name, url_args = lookup_results
        url_args['name'] = lookup_name
        optional_custom_template = url_args['id'] + ".html"
        if os.path.exists(os.path.join(directory, optional_custom_template)):
            template_name = optional_custom_template
        else: 
            template_name = '_single.html'
        template_path = os.path.join(directory, template_name)
        # do we need to initialize extra_context?
        extra_context = {}
        extra_context = flask.current_app.url_lookups_by_name[lookup_name](url_args)
        if os.path.exists(template_path):
            with codecs.open(template_path, encoding="utf-8") as template_source:
                return flask.render_template_string(template_source.read(),**extra_context)
    flask.abort(404)

            

def old_handle_request(diskpath, remainder):
    requested_file = remainder or 'index.html'
    lookup_map = flask.current_app.lookup_map.bind_to_environ(flask.request.environ)
    try:
        lookup_result = lookup_map.match()
    except NotFound:
        lookup_result = None
        
    return serve_requested_file(diskpath, requested_file, lookup_results=lookup_result)
