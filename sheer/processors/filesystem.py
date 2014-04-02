import glob

from sheer.reader import document_from_path


def documents(name, **kwargs):
    directory = kwargs['directory']
    for doc_path in glob.glob(directory+'*.md'):
        yield document_from_path(doc_path)
        

