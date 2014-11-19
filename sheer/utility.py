import os.path
import sys

import flask

this_dir = os.path.dirname(__file__)
testcase_dir = os.path.join(this_dir, 'testcases')


def get_case_path(filename):
    return os.path.join(testcase_dir, filename)


def get_case_contents(filename):
    path = get_case_path(filename)
    return file(path).read()


def path_ancestors(path):
    stop_search_at_char = 10000
    path = path.lstrip('/')
    ancestors = []

    while stop_search_at_char > 0:
        next_ancestor_end = path.rfind('/', 0, stop_search_at_char)
        ancestors.append(path[0:next_ancestor_end + 1])
        stop_search_at_char = next_ancestor_end

    return ancestors


def add_site_libs(path):
    libs_dir = os.path.join(path, '_lib')
    sys.path.append(libs_dir)


def build_search_path(root_dir, seeking_path, append=None, include_start_directory=True):
    rel_search_path = []

    rel_search_path += path_ancestors(seeking_path)

    if append and type(append) in (str, unicode):
        append_paths = [append]
    elif append:
        append_paths = append
    else:
        append_paths = []

    naked_paths = [os.path.join(root_dir, p) for p in rel_search_path]

    search_path = []

    for path in naked_paths:
        if include_start_directory:
            search_path.append(path)

        for extra_path in append_paths:
            extended_path = os.path.join(path, extra_path)
            search_path.append(extended_path)

    return search_path


def build_search_path_for_request(request,
                                  seeking_path,
                                  append=None,
                                  include_start_directory=False):
    root_dir = flask.current_app.root_dir

    return build_search_path(root_dir, seeking_path, append=append, include_start_directory=include_start_directory)


def find_in_search_path(filename, paths):
    for path in paths:
        combined_path = os.path.join(path, filename)
        if os.path.exists(combined_path):
            return combined_path


def parse_es_host_port_pair(pair):
    split_pair = pair.split(':')

    host = split_pair[0] or 'localhost'

    if len(split_pair) > 1:
        port = int(split_pair[1])
    else:
        port = 9200

    return dict(host=host, port=port)


def parse_es_hosts(packed_hosts):
    pairs = []
    for pair in packed_hosts.split(','):
        parsed = parse_es_host_port_pair(pair)
        pairs.append(parsed)

    return pairs
