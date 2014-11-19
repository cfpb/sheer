import os.path
import os
import mimetypes
import logging

from .wsgi import app_with_config


def serve_wsgi_app_with_cli_args(args, config):

        application = app_with_config(config)
        application.run(host=args.addr, port=int(args.port))
