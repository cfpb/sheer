import os.path
import importlib
import functools
import json

import werkzeug.routing

class LazyLookup(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        if 'module_name' in kwargs:
            self.module_name = kwargs['module_name']
            del self.kwargs['module_name']

    def lookup(self):
        self.lookup_module = self.processor_module = importlib.import_module(self.module_name)
        return self.lookup_module.do_lookup(**self.kwargs)

    def __getattr__(self, attrname):

        self.proxy_for = self.lookup()
        attr =  getattr(self.proxy_for, attrname)
        return attr


def add_lookups_to_sheer(app):
    json_path = os.path.join(app.root_dir, '_settings/lookups.json')
    url_rules = []
    url_lookups_by_name = {}
    permalinks_by_type = {}
    if os.path.exists(json_path):
        with file(json_path) as lookups_file:
            for name, kwarguments in json.loads(lookups_file.read()).items():

                if 'url' in kwarguments:
                    url_pattern = kwarguments['url']
                    
                    del kwarguments['url']
                    lookup_module = kwarguments.get('lookup', 'sheer.lookups.default')
                    rule = werkzeug.routing.Rule(url_pattern, endpoint=name)
                    url_rules.append(rule)
                    lookup_module = importlib.import_module(lookup_module)
                    lookup_staged = functools.partial(lookup_module.do_url, kwarguments)
                    url_lookups_by_name[name]=lookup_staged
                    if u'type' in kwarguments and kwarguments.get("permalink") == True:
                        content_type = kwarguments[u'type']
                        permalinks_by_type[content_type] = rule


                else:
                    @app.context_processor
                    def lookup_context_processor():
                        return {name: LazyLookup(**kwarguments)}

    app.lookup_map = werkzeug.routing.Map(url_rules)
    app.url_lookups_by_name = url_lookups_by_name
    app.permalinks_by_type = permalinks_by_type
