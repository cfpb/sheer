import os
import sys
import codecs

if sys.version_info[0:2] == (2, 6):
    # Python 2.6
    # the json included in 2.6 doesn't support object_pairs_hook
    from ordereddict import OrderedDict
    import simplejson as json
else:
    # Python 2.7 or higher
    from collections import OrderedDict
    import json


import copy
import glob
import importlib

from csv import DictReader

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError

from sheer.utility import add_site_libs
from sheer.processors.helpers import IndexHelper

DO_NOT_INDEX = ['_settings/',
                '_layouts/',
                '_queries/',
                '_defaults/',
                '_lib/',
                '_tests/']


def read_json_file(path):
        if os.path.exists(path):
            with codecs.open(path, 'r', 'utf-8') as json_file:
                return json.loads(json_file.read(), object_pairs_hook=OrderedDict)


class ContentProcessor(object):

    def __init__(self, name, **kwargs):
        self.name = name
        self.processor_name = kwargs['processor']
        del kwargs['processor']
        self.processor_module = importlib.import_module(self.processor_name)
        self.kwargs = kwargs

    def documents(self):
        return self.processor_module.documents(self.name, **self.kwargs)

    def mapping(self, default_mapping):
        if 'mappings' in self.kwargs:
            return read_json_file(self.kwargs['mappings'])
        if hasattr(self.processor_module, 'mappings'):
            return self.processor_module.mappings(self.name, **self.kwargs)
        else:
            return copy.deepcopy(default_mapping)


def index_document(es, index_name, processor, document):
    """
    Create the given document from the given content processor in the
    given Elasticsearch instance for the  given index.

    If the document already exists in Elasticsearch it will be updated.
    """
    # Create the document. If it already exists in Elasticsearch an
    # exception will be raised.
    try:
        es.create(index=index_name,
                doc_type=processor.name,
                id=document['_id'],
                body=document)
    except TransportError, e:
        # Elasticsearch status code 409 is DocumentAlreadyExistsException
        # Anything else and we want to bail here.
        if e.status_code != 409:
            raise e

        # If the document couldn't be created because it already exists,
        # update it instead.
        es.update(index=index_name,
                doc_type=processor.name,
                id=document['_id'],
                body={'doc': document})


def index_processor(es, index_name, default_mapping, processor, reindex=False):
    """
    Index all the documents provided by the given content processor for
    the given index in the given Elasticsearch instance.

    If reindex=True and the processor already exists the mapping in
    Elasticsearch will be destroyed and recreated and all documents will
    be created anew.
    """
    # If the mapping already exists, and we were called with the reindex
    # flag, remove the mapping.
    mapping = es.indices.get_mapping(index=index_name, doc_type=processor.name)
    if mapping and reindex:
        print "removing existing mapping for %s (%s)" % (processor.name, processor.processor_name)
        es.indices.delete_mapping(index=index_name, doc_type=processor.name)
        mapping = {}

    # Then create the mapping if it does not exist
    if not mapping:
        print "creating mapping for %s (%s)" % (processor.name, processor.processor_name)
        es.indices.put_mapping(index=index_name,
                            doc_type=processor.name,
                            body={processor.name: processor.mapping(default_mapping)})

    try:
        # Get the document iterator from the processor.
        document_iterator = processor.documents()
    except IOError:
        # A requests.exceptions.ConnectionError may be raised if the processor
        # can't connect to the API endpoint its getting the JSON from.
        document_iterator = []
        sys.stderr.write("error making connection for %s" % processor.name)

    try:
        # Iterate over the documents
        i = -1
        for i, document in enumerate(document_iterator):
            index_document(es, index_name, processor, document)
            sys.stdout.write("indexed %s %s \r" % (i + 1, processor.name))
            sys.stdout.flush()
    except ValueError:
        # There may be a ValueError (or JSONDecodeError, a subclass of
        # ValueError) raised by json.loads() with the API's supposedly JSON
        # output.
        sys.stderr.write("error reading documents for %s" % processor.name)
    else:
        sys.stdout.write("indexed %s %s \n" % (i + 1, processor.name))


def index_location(args, config):

    path = config['location']
    add_site_libs(path)

    # This whole routine is probably being too careful
    # Explicit is better than implicit, though!
    index_processor_helper = IndexHelper()
    index_processor_helper.configure(config)
    # the IndexHelper singleton can be used in processors that
    # need to talk to elasticsearch

    settings_path = os.path.join(path, '_settings/settings.json')
    default_mapping_path = os.path.join(path, '_defaults/mappings.json')
    processors_path = os.path.join(path, '_settings/processors.json')

    es = Elasticsearch(config["elasticsearch"])
    index_name = config["index"]

    # If we're given args.reindex and NOT given a list of processors to reindex,
    # we're expected to reindex everything. Delete the existing index.
    if not args.processors and args.reindex and es.indices.exists(index_name):
        print "reindexing %s" % index_name
        es.indices.delete(index_name)

    # If the index doesn't exist, create it.
    if not es.indices.exists(index_name):
        if os.path.exists(settings_path):
            es.indices.create(index=index_name, body=file(settings_path).read())
        else:
            es.indices.create(index=index_name)

    processors = []
    processor_settings = read_json_file(processors_path)

    if processor_settings:
        configured_processors = [ContentProcessor(name, **details)
                                 for name, details
                                 in processor_settings.iteritems()]

        processors += configured_processors

    glob_pattern = "".join([os.path.normpath(path), "/_*/"])
    underscored = glob.glob(glob_pattern)
    ignore_dirs = [os.path.join(path, d) for d in DO_NOT_INDEX]
    filesystem_candidates = [u for u in underscored if u not in ignore_dirs]

    for f in filesystem_candidates:
        # TODO: don't create processors for directories that
        # have a configured processor
        processor_name_starts = f[0:-1].rfind('/') + 2
        processor_name = f[processor_name_starts:-1]
        processor_args = dict(directory=f,
                              site_root=path,
                              processor="sheer.processors.filesystem")
        processors.append(ContentProcessor(processor_name, **processor_args))

    # Load default mapping (or not)
    if os.path.exists(default_mapping_path):
        try:
            default_mapping = read_json_file(default_mapping_path)
        except ValueError:
            sys.exit("default mapping present, but is not valid JSON")

    else:
        default_mapping = {}

    # If any specific content processors were selected, we run them. Otherwise
    # we run all of them.
    selected_processors = processors
    if args.processors and len(args.processors) > 0:
        selected_processors = [p for p in processors if p.name in args.processors]

    for processor in selected_processors:
        index_processor(es, index_name, default_mapping, processor, reindex=args.reindex)

