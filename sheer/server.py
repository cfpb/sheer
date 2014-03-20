import os.path, os
import mimetypes
import logging

from .wsgi import app_with_config
from .switcher import Switcher




def serve_wsgi_app_with_cli_args(args):
        root_dir = os.path.realpath(args.location)

        application = app_with_config(root_dir = root_dir)

        if args.debug:
            application.debug = True

        from paste import httpserver
        application = Switcher(root_dir, application).handle_wsgi
        httpserver.serve(application, host='127.0.0.1', port=args.port)
