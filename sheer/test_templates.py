from sheer.templates import date_formatter


class TestTemplates(object):

    def test_templates(self):
        date_string = '2012-02'
        result = date_formatter(date_string)
        assert(result == '2012-02-01')
