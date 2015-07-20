#!python

import argparse
import os
import logging
import pkg_resources

import sheer.indexer
import sheer.server
import sheer.builder

from sheer.utility import parse_es_hosts



LOCATION = os.environ.get('SHEER_LOCATION', os.getcwd())
ELASTICSEARCH_HOSTS = os.environ.get('SHEER_ELASTICSEARCH_HOSTS',
                                     'localhost:9200')
ELASTICSEARCH_INDEX = os.environ.get('SHEER_ELASTICSEARCH_INDEX', 'content')
DEBUG = bool(os.environ.get('SHEER_DEBUG', False))

VERSION = pkg_resources.require('sheer')[0].version

def run_cli():

    parser = argparse.ArgumentParser(prog='sheer',
                                     description="document loader and dev server for Sheer, a content publishing system.")

    parser.add_argument('--version', action='version', version="sheer %s" % VERSION) 
    subparsers = parser.add_subparsers()

    index_parser = subparsers.add_parser('index',
                                         help='Load content into Elasticsearch.')
    index_parser.add_argument('--reindex', '-r', action="store_true",
                              help="Recreate the index and reindex all content.")
    index_parser.add_argument('--processors', '-p', nargs='*',
                              help='Content processors to index.')
    index_parser.set_defaults(func=sheer.indexer.index_location)

    server_parser=subparsers.add_parser('serve', help= "Serve content from Elasticsearch, using configuration and templates at location.")
    server_parser.set_defaults(func=sheer.server.serve_wsgi_app_with_cli_args)
    server_parser.add_argument('--port', '-p',
            default= '7000', help="Port to run the web server on.")
    server_parser.add_argument('--addr', '-a',
            default= '0.0.0.0', help="Address to run the web server on.")

    build_parser=subparsers.add_parser('build', help='Generate a static version of this site.')
    build_parser.set_defaults(func=sheer.builder.build_with_cli_args)

    for p in [parser, index_parser, server_parser]:
        p.add_argument('--debug', help="Print debugging output to the console.", action='store_true', default=DEBUG)
        p.add_argument('--location', '-l', default=LOCATION, help="Directory you want to operate on. You can also set the SHEER_LOCATION environment variable.")
        p.add_argument('--elasticsearch', '-e', default=ELASTICSEARCH_HOSTS, help="Elasticsearch host:port pairs. Separate hosts with commas. Default is localhost:9200. You can also set the SHEER_ELASTICSEARCH_HOSTS environment variable.")
        p.add_argument('--index', '-i', default=ELASTICSEARCH_INDEX, help="Elasticsearch index name. Default is 'content'. You can also set the SHEER_ELASTICSEARCH_INDEX environment variable.")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig()
        logger = logging.getLogger("")
        logger.setLevel(logging.DEBUG)
        tracer = logging.getLogger('elasticsearch.trace')
        tracer.setLevel(logging.DEBUG)
        tracer.addHandler(logging.FileHandler('/tmp/elasticsearch-py.sh'))

    config = dict(debug=args.debug,
                  location=os.path.join(os.getcwd(), args.location),
                  elasticsearch=parse_es_hosts(args.elasticsearch),
                  index=args.index)
    args.func(args, config)

if __name__ == '__main__':
    run_cli()
