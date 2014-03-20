import os.path
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
        next_ancestor_end= path.rfind('/',0, stop_search_at_char)
        ancestors.append(path[0:next_ancestor_end+1])
        stop_search_at_char = next_ancestor_end

    return ancestors
        

def build_search_path(root_dir, seeking_path, append=None, include_start_directory=False):
    rel_search_path = []

    rel_search_path += path_ancestors(seeking_path)

    if append:
        rel_search_path = [os.path.join(p,append) for p in rel_search_path]

    search_path = [os.path.join(root_dir, p) for p in rel_search_path]

    if append and include_start_directory:
        rel_seeking_path = seeking_path.lstrip('/')
        complete_path = os.path.join(root_dir, rel_seeking_path)
        dirname = os.path.dirname(complete_path) + '/'
        search_path.insert(0,dirname)

    return search_path


def build_search_path_for_request(request,
                                  seeking_path,
                                  dirname='.',
                                  include_start_directory=False):
    root_dir = flask.current_app.root_dir

    return build_search_path(root_dir, dirname, include_start_directory=include_start_directory)


def find_in_search_path(filename, paths):
    for path in paths:
        combined_path = os.path.join(path, filename)
        if os.path.exists(combined_path):
            return combined_path
