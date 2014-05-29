import flask

def filter_dsl_from_multidict(multidict):
    filter_keys = [k for k in multidict.keys() if k.startswith('filter_')]
    if len(filter_keys) > 0:
        dsl = {"bool": {"must":[], "should":[], "must_not":[]}}
        for key in filter_keys:
            field = key[7:]
            values = multidict.getlist(key)
            for val in values:
                if val:
                    term_clause = {"term":{}}
                    term_clause["term"][field] = val
                    dsl["bool"]["should"].append(term_clause)

        return dsl
    
def selected_filters_from_multidict(multidict, field):
    return multidict.getlist('filter_'+ field)

def selected_filters_for_field(fieldname):
    multidict = flask.request.args
    return selected_filters_from_multidict(multidict, fieldname)

def is_filter_selected(fieldname, value):
    multidict = flask.request.args
    return value in selected_filters_from_multidict(multidict, fieldname)

def add_filter_utilities(app):

    @app.context_processor
    def filter_utility_context():
        return {'selected_filters_for_field': selected_filters_for_field,
                'is_filter_selected': is_filter_selected}
    
