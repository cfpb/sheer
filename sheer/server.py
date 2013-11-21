import os.path, os
import mimetypes
import logging

import markdown


from sheer import reader, query, exceptions, utility, templates
from sheer.site import Site


def serve_wsgi_app_with_cli_args(args):
        root_dir = os.path.realpath(args.location)
        site = Site(root_dir)
        application =  site.handle_wsgi
        if args.debug:
            from werkzeug.debug import DebuggedApplication
            application = DebuggedApplication(application, evalex=True)

        from paste import httpserver
        httpserver.serve(application, host='127.0.0.1', port=args.port)
