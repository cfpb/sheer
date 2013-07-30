import os
import os.path

import mimetypes

from webob import Request, Response
from jinja2 import FileSystemLoader, Environment
import markdown

from sheer.render import render_html
from sheer.templates import date_formatter
from sheer.decorators import memoized
from sheer.query import QueryFinder
from sheer.searchpath import SearchPath


SPECIAL_DIRECTORIES = ['_defaults',
                       '_queries',
                       '_layouts',
                       '_settings',
                       '.git']


def filter_out_special_dirs(dirs):
    for special in SPECIAL_DIRECTORIES:
        if special in dirs:
            dirs.remove(special)


def scrub_name(name):
    if name.startswith('_'):
        name = name[1:]
    return name.replace('-', '_')


class Site(object):

    def __init__(self, path, elasticsearch_index=None):
        cwd = os.getcwd()
        self.site_root = os.path.normpath(os.path.join(cwd, path))
        self.elasticsearch_index = elasticsearch_index
        self.directories = {}

        for here, dirs, files in os.walk(self.site_root):
            filter_out_special_dirs(dirs)

            parent_dir, dirname = os.path.split(here)
            relparent = os.path.relpath(parent_dir, self.site_root)
            if relparent == '.':
                relparent = '/'
            else:
                relparent = '/' + relparent

            parent = self.directories.get(relparent)

            if dirname.startswith('_'):
                corrected_path = parent_dir + '/' + dirname[1:]
                relpath = os.path.relpath(corrected_path, self.site_root)
                directory = IndexableDirectory(here, self, url=relpath,
                                               parent=parent)
                if parent:
                    parent.add_child_indexable(dirname[1:], directory)
            else:
                relpath = os.path.relpath(here, self.site_root)
                if relpath == '.':
                    relpath = '/'
                else:
                    relpath = "/" + relpath

                directory = Directory(here, self, url=relpath, parent=parent)
                if parent:
                    parent.add_child_dir(dirname, directory)

            self.directories[relpath] = directory
            for filename in files:
                if filename.startswith('_'):
                    basename, ext = os.path.splitext(filename)
                    if ext.lower() == '.csv':
                        complete_path = directory.join_path(filename)
                        indexable_file = IndexableFile(complete_path,
                                                       self, parent=directory)
                        directory.add_child_indexable(filename[1:],
                                                      indexable_file)

        self.root = self.directories['/']

    def indexables(self):
        return self.root.indexables()

    def handle_wsgi(self, environ, start_response):
        directory_key, filename = os.path.split(environ['PATH_INFO'])
        environ['ELASTICSEARCH_INDEX'] = self.elasticsearch_index
        environ['SITE'] = self

        if directory_key in self.directories:
            environ['PATH_INFO'] = environ['PATH_INFO'][len(directory_key):]
            return self.directories[directory_key].handle_wsgi(environ,
                                                               start_response)


class AncestryMixin(object):

    def parents(self):
        if self.parent:
            parents = [self.parent]
            current_parent = self.parent
            while current_parent.parent:
                parents.append(current_parent.parent)
                current_parent = current_parent.parent
            return parents
        else:
            return []


class Directory(AncestryMixin):

    def __init__(self, physical_path, site, url, parent=None):
        self.site = site
        self.parent = parent
        self.physical_path = physical_path
        self.child_dirs = {}
        self.child_indexables = {}
        self.url = url

        if parent:
            self.name = scrub_name(os.path.split(self.physical_path)[1])
        else:
            self.name = '(root)'

    def handle_wsgi(self, environ, start_response):
        request = Request(environ)
        requested_path = self.join_url_to_path(request.path)

        isdir = os.path.isdir(requested_path)

        if isdir and not requested_path.endswith('/'):
            redirect_to = request.host_url + self.url + request.path + '/'
            response = Response(location=redirect_to, status=302)
            return response(environ, start_response)

        if isdir:
            requested_path += 'index.html'

        base, ext = os.path.splitext(requested_path)
        canonical_ext = ext.lower()

        response = Response(content_type='text/html')

        if ext:
            mime = mimetypes.types_map.get(canonical_ext)
            if type:
                response.headers['Content-type'] = mime

        if canonical_ext not in ['.html']:
            response.body = file(requested_path, 'rb').read()

        else:
            response.charset = 'utf-8'
            context = self.context_for_request(request)
            response.text = render_html(
                requested_path, self.jinja2_environment(), context, request)
        return response(environ, start_response)

    def join_path(self, path):
        return os.path.join(self.physical_path, path)

    def join_url_to_path(self, urlpath):

        if urlpath.startswith('/'):
            urlpath = urlpath[1:]

        return self.join_path(urlpath)

    def add_child_dir(self, name, directory):
        self.child_dirs[name] = directory

    def add_child_indexable(self, name, indexable):
        self.child_indexables[name] = indexable

    def indexables(self):
        for key in self.child_indexables:
            yield self.child_indexables[key]

        for key in self.child_dirs:
            for indexable in self.child_dirs[key].indexables():
                yield indexable

    @memoized
    def generate_searchpath(self, dirname):
        paths = [self.join_path(dirname)]

        for ancestor in self.parents():
            paths.append(ancestor.join_path(dirname))

        return SearchPath(paths)

    @memoized
    def jinja2_environment(self):
        template_search_path = self.generate_searchpath('_layouts')
        loader = FileSystemLoader(template_search_path.paths)
        environment = Environment(loader=loader)

        environment.filters['markdown'] = markdown.markdown
        environment.filters['date'] = date_formatter

        return environment

    def context_for_request(self, request):
        context = {}
        context['queries'] = self.queryfinder_for_request(request)
        return context

    @memoized
    def queryfinder_for_request(self, request):
        searchpath = self.generate_searchpath('_queries')

        return QueryFinder(searchpath, request)


class IndexableMixin(object):

    def index_name(self):
        chain = self.parents()[:-1]
        chain.reverse()
        chain.append(self)
        index_name = '_'.join([p.name for p in chain])
        return index_name

    def indexer(self):
        return self.indexer_class(self)


class IndexableDirectory(Directory, IndexableMixin):

    def __init__(self, *args, **kwargs):
        super(IndexableDirectory, self).__init__(*args, **kwargs)
        from sheer import indexer
        self.indexer_class = indexer.DirectoryIndexer


class IndexableFile(IndexableMixin, AncestryMixin):

    def __init__(self, physical_path, site, parent):
        self.site = site
        self.parent = parent
        self.physical_path = physical_path
        directory, filename = os.path.split(physical_path)
        self.name = scrub_name(os.path.splitext(filename)[0])

        from sheer import indexer
        self.indexer_class = indexer.CSVFileIndexer


def print_with_indent(indentlevel, text):
    print ' ' * indentlevel,   text


def print_directory_tree(directory, indentlevel=0):
    print_with_indent(indentlevel, directory.name)
    for indexable in directory.child_indexables:
        print_with_indent(
            indentlevel + 4,
            directory.child_indexables[indexable].name + '(indexable)')
    for child_dir in directory.child_dirs:
        print_directory_tree(directory.child_dirs[
                             child_dir], indentlevel=indentlevel + 4)


def inspect_site(path):
    site = Site(path)
    print_directory_tree(site.root)


def inspect_with_args(args):
    inspect_site(args.location)
