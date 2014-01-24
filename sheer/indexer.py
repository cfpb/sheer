import os
import sys
import codecs
import json
import logging
import copy
import urlparse
import glob
import importlib

from csv import DictReader

from elasticsearch import Elasticsearch

from sheer.site import Site
from sheer import reader


def read_json_file(path):
        if os.path.exists(path):
            with codecs.open(path, 'r', 'utf-8') as json_file:
                    return json.loads(json_file.read())


class Indexer(object):

    def __init__(self, indexable):
        self.path = indexable.physical_path
        self.name = indexable.index_name()

    def index_documents_to(self, es):
        count = 0
        for document in self.documents():
            if document.get('published', True):
                es.create(index="content",
                          doc_type=self.name,
                          id=document['_id'],
                          body=document)
                count += 1
                sys.stdout.write("indexed %s %s \r" % (count, self.name))
                sys.stdout.flush()

        sys.stdout.write("indexed %s %s \n" % (count, self.name))

    def documents(self):
        return []

    def load_mapping_file(self, mapping_path):

        try:
            return read_json_file(mapping_path)

        except IOError:
            logging.debug("could not read %s" % mapping_path)

        except ValueError:
            logging.debug("could not parse JSON in %s" % mapping_path)

    def additional_mappings(self):
        if hasattr(self, 'additional_mappings_path'):
                mapping_path = self.additional_mappings_path()
                return self.load_mapping_file(mapping_path)

    def __str__(self):
        return "<{0}, {1}>".format(type(self).__name__, self.name)


class DirectoryIndexer(Indexer):

    def additional_mappings_path(self):
        return os.path.join(self.path, 'mappings.json')

    def documents(self):
        for document_path in glob.glob(self.path + '/*.md'):
            yield reader.document_from_path(document_path)


class CSVFileIndexer(Indexer):

    def additional_mappings_path(self):
        return self.path + '.mappings.json'

    def documents(self):
        with file(self.path) as csvfile:
            next_id = 1
            for row in DictReader(csvfile):
                row['_id'] = next_id
                next_id += 1
                yield row


class PageIndexer(Indexer):
    name = "pages"

    def __init__(self):
        pages = []

    def add(self, path):
        self.pages.append(path)


class CustomIndexer(Indexer):
    def __init__(self, name, **kwargs):
        self.name=name
        self.processor_name = kwargs['processor']
        del kwargs['processor']
        self.processor_module = importlib.import_module('sheer.processors.' + self.processor_name)
        if 'extra_mappings_file' in kwargs:
            self.mappings_path = kwargs['extra_mappings_file']
            del kwargs['extra_mappings_file']
        self.kwargs = kwargs

    def documents(self):
        return self.processor_module.documents(self.name,**self.kwargs)

    def additional_mappings_path(self):
        if hasattr(self, 'mappings_path'):
            return self.mappings_path
        return None


def path_to_type_name(path):
    path = path.replace('/_', '_')
    path = path.replace('/', '_')
    path = path.replace('-', '_')
    return path


def index_args(args):
    index_location(args.location)



def index_location(path):

    settings_path = os.path.join(path, '_settings/settings.json')
    default_mapping_path = os.path.join(path, '_defaults/mappings.json')
    custom_processors_path = os.path.join('_settings/custom_processors.json')

    es = Elasticsearch()

    if es.indices.exists('content'):
        es.indices.delete('content')
    if os.path.exists(settings_path):
        es.indices.create(index="content", body=file(settings_path).read())
    else:
        es.indices.create(index="content")

    page_indexer = PageIndexer()
    indexers = [page_indexer]

    site = Site(path)
    indexables = site.indexables()
    indexers = [i.indexer() for i in indexables]

    custom_processors = read_json_file(custom_processors_path)
    if custom_processors:
        for name, details in custom_processors.iteritems():
            indexer = CustomIndexer(name, **details)
            indexers.append(indexer)

    # Load default mapping (or not)
    if os.path.exists(default_mapping_path):
        try:
            default_mapping = read_json_file(default_mapping_path)
        except ValueError:
            sys.exit("default mapping present, but is not valid JSON")

    else:
        default_mapping = {}

    for indexer in indexers:
            mappings = copy.deepcopy(default_mapping)
            if hasattr(indexer, 'additional_mappings'):
                additional_mappings = indexer.additional_mappings()
                if additional_mappings:
                    for key in additional_mappings.keys():
                        if key in mappings:
                            mappings[key].update(additional_mappings[key])
                        else:
                            mappings[key] = additional_mappings[key]
            es.indices.put_mapping(index='content', doc_type=indexer.name, body={indexer.name:mappings})
            print "creating mapping for %s"  % (indexer.name )
            indexer.index_documents_to(es)
