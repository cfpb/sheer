import os.path, os
import mimetypes
import logging

from flask import Flask

import markdown


from sheer import reader, query, exceptions, utility, templates
from sheer.site import Site


def create_flask_handlers(app):
    for path in os.listdir('.'):
        if path[0] in ['.','_']:
            continue
        if os.path.isdir(path):
            for root, dirs, files in os.walk('path'):
                print root

def serve_wsgi_app_with_cli_args(args):
        root_dir = os.path.realpath(args.location)
        os.chdir(root_dir)
        site = Site(root_dir)
        app = Flask(__name__.split('.')[0])
        if args.debug:
            app = Flask(__name__.split('.')[0], debug=True)

        create_flask_handlers(app)

        from paste import httpserver
        httpserver.serve(app, host='127.0.0.1', port=args.port)
