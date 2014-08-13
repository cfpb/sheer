import flask
import re
import calendar
import datetime
from dateutil.parser import parse

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
        
        # Validate date range input
        
        # First check if both date_lte and date_gte are present
        # If the 'start' date is after the 'end' date, swap them
        if 'date' in range_clause['range']:
            if all(x in range_clause['range']['date'] for x in ('lte', 'gte')) and \
             parse(range_clause['range']['date']['gte'], default=datetime.date.today().replace(day=1)) > \
             parse(range_clause['range']['date']['lte'], default=datetime.date.today().replace(day=1)):
                range_clause['range']['date']['gte'], range_clause['range']['date']['lte'] = \
                range_clause['range']['date']['lte'], range_clause['range']['date']['gte']
            # If either date matches the YYYY-M[M] format, append the appropriate day
            if 'lte' in range_clause['range']['date'] and \
            re.compile("^[0-9]{4}-[0-9]{1,2}$").match(range_clause['range']['date']['lte']):
                year, month = range_clause['range']['date']['lte'].split('-')
                last_day_of_month = calendar.monthrange(int(year), int(month))[1]
                range_clause['range']['date']['lte'] += "-{}".format(last_day_of_month)
            if 'gte' in range_clause['range']['date'] and \
            re.compile("^[0-9]{4}-[0-9]{1,2}$").match(range_clause['range']['date']['gte']):
                range_clause['range']['date']['gte'] += "-1"
        dsl["and"].append(range_clause)
    return dsl
    
def selected_filters_from_multidict(multidict, field):
    return [k for k in multidict.getlist('filter_'+ field) if k]

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
    
