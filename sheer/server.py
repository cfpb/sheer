import os.path, os
import mimetypes
import logging

from .wsgi import app_with_config




def serve_wsgi_app_with_cli_args(args):
        root_dir = os.path.realpath(args.location)

        application = app_with_config(root_dir = root_dir)

        if args.debug:
            application.debug = True

        application.run(port=int(args.port))
