from werkzeug.datastructures import MultiDict

from sheer import filters

class testArgParsing(object):
    def setup(self):
        self.args = MultiDict([('filter_category','cats'),
                               ('filter_category','dogs'),
                               ('filter_range_date_lte', '2014-6-1'),
                               ('filter_range_comment_count_gt', '100')])

    def test_args_to_filter_dsl(self):
        filter_dsl = filters.filter_dsl_from_multidict(self.args)
        assert('bool' in filter_dsl['and'][0])
        assert('must' in filter_dsl['and'][0]['bool'])
        value1 = filter_dsl['and'][0]['bool']['should'][0]['term']['category']
        value2 = filter_dsl['and'][0]['bool']['should'][1]['term']['category']
        assert('cats' in [value1, value2])
        assert('dogs' in [value1, value2])

    def test_range_args(self):
        filter_dsl = filters.filter_dsl_from_multidict(self.args)
        assert('range' in filter_dsl['and'][1])
        assert('date' in filter_dsl['and'][1]['range'])
        assert('comment_count' in filter_dsl['and'][1]['range'])
        assert('2014-6-1' == filter_dsl['and'][1]['range']['date']['lte'])
        assert('100' == filter_dsl['and'][1]['range']['comment_count']['gt'])

    def test_filters_for_field(self):
        selected = filters.selected_filters_from_multidict(self.args, 'category')
        assert (('cats') in selected)
        assert (('dogs') in selected)

    def test_date_validation_incorrect_range(self):
        args = MultiDict([('filter_range_date_gte', '2014-6'),
                          ('filter_range_date_lte', '2013-6')])
        filter_dsl = filters.filter_dsl_from_multidict(args)
        assert(filter_dsl['and'][0]['range']['date']['gte'] == '2013-6')
        assert(filter_dsl['and'][0]['range']['date']['lte'] == '2014-6')

    def test_date_validation_correct_range(self):
        args = MultiDict([('filter_range_date_gte', '2013-6'),
                          ('filter_range_date_lte', '2014-6')])
        filter_dsl = filters.filter_dsl_from_multidict(args)
        assert(filter_dsl['and'][0]['range']['date']['gte'] == '2013-6')
        assert(filter_dsl['and'][0]['range']['date']['lte'] == '2014-6')

    def test_date_validation_with_days_correct_range(self):
        args = MultiDict([('filter_range_date_gte', '2014-1-23'),
                          ('filter_range_date_lte', '2014-6-23')])
        filter_dsl = filters.filter_dsl_from_multidict(args)
        assert(filter_dsl['and'][0]['range']['date']['gte'] == '2014-1-23')
        assert(filter_dsl['and'][0]['range']['date']['lte'] == '2014-6-23')

    def test_date_validation_with_days_incorrect_range(self):
        args = MultiDict([('filter_range_date_gte', '2014-6-23'),
                          ('filter_range_date_lte', '2014-1-23')])
        filter_dsl = filters.filter_dsl_from_multidict(args)
        assert(filter_dsl['and'][0]['range']['date']['gte'] == '2014-1-23')
        assert(filter_dsl['and'][0]['range']['date']['lte'] == '2014-6-23')