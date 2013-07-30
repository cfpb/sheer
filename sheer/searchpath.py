import os, os.path

class SearchPath(object):
    def __init__(self, paths):
        self.paths = paths


    def find(self, name):
        for path in self.paths:
            combined_path = os.path.join(path, name)
            if os.path.exists(combined_path):
                return combined_path
