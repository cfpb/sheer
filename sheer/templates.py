import datetime
import flask
from dateutil import parser

from jinja2.loaders import FileSystemLoader


def date_formatter(value, format="%Y-%m-%d"):
    if type(value) not in [datetime.datetime, datetime.date]:
        dt = parser.parse(value)
    else:
        dt = value

    return dt.strftime(format)


class SheerTemplateLoader(FileSystemLoader):

    def get_source(self, environment, template):
        contents, filename, uptodate = super(SheerTemplateLoader, self).get_source(environment, template)
        return contents, flask.request.path, uptodate
