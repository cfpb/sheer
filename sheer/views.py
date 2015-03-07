import os.path
import codecs
import mimetypes
import re

import flask
from flask import request
from werkzeug.exceptions import HTTPException, NotFound

from elasticsearch.exceptions import NotFoundError

from .utility import build_search_path, build_search_path_for_request, find_in_search_path
from .query import QueryHit

always_404_pattern = re.compile(r'/[._]')

def do_lookup(name, doc_type, **search_params):
    es = flask.current_app.es
    es_index = flask.current_app.es_index

    lookup_name = name
    doc_type = doc_type
    id = search_params['id']

    try:
        document = es.get(index=es_index, doc_type=doc_type, id=id)
        hit = QueryHit(document)
        return {lookup_name: hit}
    except NotFoundError:
        return None


def handle_request(lookup_name=None, lookup_config=None, **kwargs):
    lookup_doc = None
    root_dir = flask.current_app.root_dir
    request_path = request.path

    if always_404_pattern.search(request_path):
        return serve_error_page(404)

    if request_path.endswith('/'):
            request_path += ('index.html')

    translated_path = os.path.join(root_dir, request_path[1:])

    if os.path.isdir(translated_path) and not request_path.endswith('/'):
            return flask.redirect(request_path[1:] + '/')

    if not request_path.endswith('.html') and os.path.exists(translated_path):
        mime, encoding = mimetypes.guess_type(translated_path)
        if mime:
            return flask.send_file(translated_path), 200, {'Content-Type': mime}
        else:
            return flask.send_file(translated_path), 200, {'Content-Type': 'application/unknown'}

    if lookup_name:
        doc_type = lookup_config['type']
        search_params = lookup_config.copy()
        del search_params['url']
        del search_params['type']

        lookup_doc = do_lookup(lookup_name, doc_type, **kwargs)

    template_candidates = [translated_path]
    if lookup_doc:
        template_candidates += build_search_path(
            root_dir, request.path, append='_single.html', include_start_directory=False)

    try:

        template_path = next(
            t for t in template_candidates if os.path.exists(t))

        if os.path.exists(template_path):
            template_context = {}
            template_context.update(lookup_doc or {})

            with codecs.open(template_path, encoding="utf-8") as template_source:
                return flask.render_template_string(template_source.read(), **template_context)

    except StopIteration:
        return serve_error_page(404)


def serve_error_page(error_code):
    request = flask.request
    # TODO: this seems silly
    # We shouldn't even need to send the request object,
    # and the second argument should usually be request.path anyways
    search_path = build_search_path_for_request(
        request, request.path, append=['_layouts', '_includes'], include_start_directory=True)
    template_path = find_in_search_path('%s.html' % error_code, search_path)

    if template_path:
        with codecs.open(template_path, encoding="utf-8") as template_source:
            return flask.render_template_string(template_source.read()), error_code
    else:
        return "Please provide a %s.html!" % error_code, error_code
