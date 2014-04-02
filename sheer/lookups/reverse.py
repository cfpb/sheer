import flask

class Backwards(object):
    def __init__(self, document):
        self.document = document

    def __getattr__(self, attrname):
        if hasattr(self.document, attrname):
            val = getattr(self.document,attrname)
            if type(val) in (string, unicode):
                return reversed(val)

def do_lookup(**kwargs):
    return Backwards(**kwargs)


