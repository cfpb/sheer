import flask
import re

def filter_dsl_from_multidict(multidict):
    # Split the filters between 'range' and 'bool', making sure the query value isn't blank
    bool_filter_keys = [r for r in [k for k in multidict.keys() if re.compile("^filter_(?!range_)").match(k)] \
                         if multidict[r]]
    range_filter_keys = [r for r in [k for k in multidict.keys() if re.compile("^filter_range_").match(k)] \
                         if multidict[r]]

    dsl = {}
    if bool_filter_keys or range_filter_keys:
        dsl["and"] = []
    if bool_filter_keys:
        bool_clause = {"bool":{"must":[], "should":[], "must_not":[]}}
        for key in bool_filter_keys:
            field = key.replace('filter_', '')
            values = multidict.getlist(key)
            for val in values:
                term_clause = {"term":{}}
                term_clause["term"][field] = val
                bool_clause["bool"]["should"].append(term_clause)
        dsl["and"].append(bool_clause)


    if range_filter_keys:
        range_clause = {"range":{}}
        for key in range_filter_keys:
            full_field = key.replace('filter_range_', '')
            # We account for potential underscores in the field name itself e.g. comment_count
            operator = full_field[full_field.rfind('_')+1:]
            field = full_field[:full_field.rfind('_')]
            if field not in range_clause["range"]:
                range_clause["range"][field] = {}
            # If there are multiples of the same date filter, this will take the first
            value = multidict.getlist(key)[0]
            range_clause["range"][field][operator] = value
        dsl["and"].append(range_clause)

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
    
