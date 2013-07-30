import os.path, os
import mimetypes
import logging

import markdown


from sheer import reader, query, exceptions, utility, templates
from sheer.site import Site


def response_for_path(physical_path, request):

    return response

        
def serve_wsgi_app_with_cli_args(args):
        root_dir = os.path.realpath(args.location)
        es_index = args.elasticsearch_index

        site = Site(root_dir, es_index)
        application =  site.handle_wsgi
        if args.debug:
            from werkzeug.debug import DebuggedApplication
            from werkzeug.serving import run_simple
            application = DebuggedApplication(application, evalex=True)
            run_simple('127.0.0.1', int(args.port), application, use_debugger=True, use_reloader=True)


        from paste import httpserver
        httpserver.serve(application, host='127.0.0.1', port=args.port)
