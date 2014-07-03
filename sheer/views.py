import os.path
import codecs

import flask
from flask import request
from werkzeug.exceptions import HTTPException, NotFound

def serve_requested_file(directory, requested_file, lookup_results=None):
    complete_path = os.path.join(directory, requested_file)
    if os.path.exists(complete_path):
        if requested_file.lower().endswith('.html'):
            with codecs.open(complete_path, encoding="utf-8") as template_source:
                return flask.render_template_string(template_source.read())
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

            

def handle_request(diskpath, remainder):
    requested_file = remainder or 'index.html'
    lookup_map = flask.current_app.lookup_map.bind_to_environ(flask.request.environ)
    try:
        lookup_result = lookup_map.match()
    except NotFound:
        lookup_result = None
        
    return serve_requested_file(diskpath, requested_file, lookup_results=lookup_result)
