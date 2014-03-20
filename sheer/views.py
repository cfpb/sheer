import os.path
import codecs

import flask
from flask import request

def serve_requested_file(directory, requested_file):
    if requested_file.lower().endswith('.html'):
        path = os.path.join(directory, requested_file)
        with codecs.open(path, encoding="utf-8") as template_source:
            return flask.render_template_string(template_source.read())
    else:
        return flask.send_from_directory(directory, requested_file)

def handle_request(diskpath, remainder):
    requested_file = remainder or 'index.html'
    if os.path.exists(requested_file):
        return serve_requested_file(diskpath, requested_file)
    else:
        flask.abort(404)
    return "looking for %s in %s?" % (remainder, diskpath)
