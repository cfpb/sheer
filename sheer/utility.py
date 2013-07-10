import os.path

this_dir = os.path.dirname(__file__)
testcase_dir = os.path.join(this_dir, 'testcases')

def get_case_path(filename):
    return os.path.join(testcase_dir, filename)

def get_case_contents(filename):
    path = get_case_path(filename)
    return file(path).read()
