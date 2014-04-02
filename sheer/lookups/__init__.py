import os.path
import importlib
import json

import werkzeug.routing

class LazyLookup(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        if 'module_name' in kwargs:
            self.module_name = kwargs['module_name']
            self._cached = None
            del self.kwargs['module_name']

    def lookup(self):
        if not self._cached:
            self.lookup_module = self.processor_module = importlib.import_module(self.module_name)
            self._cached = self.lookup_module.do_lookup(**self.kwargs)
        return self._cached

    def __getattr__(self, attrname):
        proxy_for = self.lookup()
        return getattr(self.proxy_for, attrname)

        

def add_lookups_to_sheer(app):
    json_path = os.path.join(app.root_dir, '_settings/lookups.json')
    url_rules = []
    if os.path.exists(json_path):
        with file(json_path) as lookups_file:
            for name, kwarguments in json.loads(lookups_file.read()).items():

                if 'url' in kwarguments:
                    rule = werkzeug.routing.Rule(kwarguments['url'], endpoint= kwarguments['type'])
                    
                @app.context_processor
                def lookup_context_processor():
                    return {name: LazyLookup(**kwarguments)}
