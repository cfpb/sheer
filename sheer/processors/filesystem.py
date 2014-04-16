import os.path
import json
import glob

from sheer.reader import document_from_path


def documents(name, **kwargs):
    directory = kwargs['directory']
    for doc_path in glob.glob(directory+'*.md'):
        yield document_from_path(doc_path)
        

def mappings(name, **kwargs):
    site_root = kwargs.get('site_root', '.')
    mappings_path = os.path.join(site_root, '_defaults/%s_mappings.json' % name)
    if os.path.exists(mappings_path):
        with file(mappings_path) as mappings_file:
            return json.loads(mappings_file.read())
        
