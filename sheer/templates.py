import datetime
import flask
from dateutil import parser



def date_formatter(value, format="%Y-%m-%d"):
    if type(value) not in [datetime.datetime, datetime.date]:
        dt = parser.parse(value, default=datetime.date.today().replace(day=1))
    else:
        dt = value

    return dt.strftime(format)

