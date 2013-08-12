import os.path, os
import mimetypes
import logging

import markdown


from sheer import reader, query, exceptions, utility, templates
from sheer.site import Site


def response_for_path(physical_path, request):
    base, ext = os.path.splitext(physical_path)
    canonical_ext=ext.lower()
    
    response= Response(content_type='text/html')

    if ext:
        mime = mimetypes.types_map.get(canonical_ext)
        if type:
            response.headers['Content-type']= mime

    if canonical_ext not in ['.html']:
        response.body= file(physical_path, 'rb').read()

    else:
        response.charset='utf-8'
        response.text = render_html(physical_path, request)


    return response

        


def serve_wsgi_app_with_cli_args(args):
        root_dir = os.path.realpath(args.location)
        site = Site(root_dir)
        application =  site.handle_wsgi
        if args.debug:
            from werkzeug.debug import DebuggedApplication
            application = DebuggedApplication(application, evalex=True)

        from paste import httpserver
        httpserver.serve(application, host='127.0.0.1', port=args.port)
