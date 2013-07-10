import os

SPECIAL_DIRECTORIES = ['_defaults', '_queries', '_layouts']


class Indexer(object):
    def __init__(self, path, name):
        self.path = path
        self.name = name

    def __str__(self):
        return "<{0}, {1}>".format(type(self).__name__, self.name)


class DirectoryIndexer(Indexer):
    pass

class FileIndexer(Indexer):
    pass

class PageIndexer(Indexer):
    name= "pages"

    def __init__(self):
        pages = []

    def add(self, path):
        self.pages.append(path)


def path_to_type_name(path):
    path=path.replace('/_', '_')
    path=path.replace('/', '_')
    path=path.replace('-','_')
    return path

def index_args(args):
    index_location(args.location, args.elasticsearch_host)

def index_location(path, es):
    page_indexer = PageIndexer()
    indexers = [page_indexer]

    for root, dirs, files in os.walk(path):
        relative_root = root[len(path)+1:]
        for dir in dirs:
            relative_dir= '%s/%s' % (relative_root, dir)
            complete_dir= os.path.join(path, relative_dir)
            if dir.startswith('_') and dir not in SPECIAL_DIRECTORIES:
                indexer = DirectoryIndexer(complete_dir, path_to_type_name(relative_dir))
                indexers.append(indexer)

        for filename in files:
            complete_path=os.path.join(root, filename)
            basename, ext = os.path.splitext(filename)
            if filename.startswith('_'):
                path_no_ext= os.path.join(relative_root, basename)
                complete_path=os.path.join(root, filename)
                indexer= FileIndexer(complete_path, path_to_type_name(path_no_ext))
                indexers.append(indexer)

            elif ext.lower() in ['md','html']: 
                page_indexer.add(complete_path)
    if indexers:
        print "Found indexable content:"
        for indexer in indexers:
            print indexer
