from werkzeug.datastructures import MultiDict

from .filters import filter_dsl_from_multidict


class testUrlArgstoFilters:
    def test_simple_filters(self):
        args = MultiDict([('filter_category','cats'),('filter_category','dogs')])
        filter_dsl = filter_dsl_from_multidict(args)
        assert('bool' in filter_dsl)
        assert('must' in filter_dsl['bool'])
        values = filter_dsl['bool']['must'][0]['term']['category']
        assert('cats' in values)
        assert('dogs' in values)



