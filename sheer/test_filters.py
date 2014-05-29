from werkzeug.datastructures import MultiDict

from sheer import filters

class testArgParsing(object):
    def setup(self):
        self.args = MultiDict([('filter_category','cats'),('filter_category','dogs')])

    def test_args_to_filter_dsl(self):
        filter_dsl = filters.filter_dsl_from_multidict(self.args)
        assert('bool' in filter_dsl)
        assert('must' in filter_dsl['bool'])
        value1 = filter_dsl['bool']['should'][0]['term']['category']
        value2 = filter_dsl['bool']['should'][1]['term']['category']
        assert('cats' in [value1, value2])
        assert('dogs' in [value1, value2])

    def test_filters_for_field(self):
        selected = filters.selected_filters_from_multidict(self.args, 'category')
        assert (('cats') in selected)
        assert (('dogs') in selected)
