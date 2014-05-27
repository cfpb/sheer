
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
