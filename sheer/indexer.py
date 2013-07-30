import os
import sys
import codecs
import json
import logging
import copy
import urlparse
import glob
from csv import DictReader

import requests

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

    def index_documents_to(self, index_url):
        count = 0
        for document in self.documents():
            destination_path = '%s/%s' % (self.name, document['_id'])
            destination_url = urlparse.urljoin(index_url, destination_path)
            if document.get('published', True):
                requests.put(destination_url, json.dumps(document))
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


def path_to_type_name(path):
    path = path.replace('/_', '_')
    path = path.replace('/', '_')
    path = path.replace('-', '_')
    return path


def index_args(args):
    index_location(args.location, args.elasticsearch_index)


def index_location(path, es):
    settings_path = os.path.join(path, '_settings/settings.json')
    requests.delete(es)
    if os.path.exists(settings_path):
        requests.put(es, file(settings_path).read())
    else:
        requests.put(es)

    page_indexer = PageIndexer()
    indexers = [page_indexer]

    site = Site(path)
    indexables = site.indexables()
    indexers = [i.indexer() for i in indexables]

    # Load default mapping (or not)
    default_mapping_path = os.path.join(path, '_defaults/mappings.json')
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
            index_url = urlparse.urljoin(es, indexer.name + '/_mapping')
            response = requests.put(
                index_url, json.dumps({indexer.name: mappings}))
            print "creating mapping for %s at %s [%s]" % (indexer.name, index_url, response.status_code)
            indexer.index_documents_to(es)
            logging.debug(response.content)
