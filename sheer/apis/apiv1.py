import json

from flask.ext import restful
import flask


from sheer.query import QueryFinder, QueryJsonEncoder


def default_query_finder():
    return QueryFinder()


def custom_json_output(data, code, headers=None):
    dumped = json.dumps(data, cls=QueryJsonEncoder)
    resp = flask.make_response(dumped, code)
    resp.headers.extend(headers or {})
    return resp


def add_to_sheer(app):
    api = restful.Api(app)

    class QueryResource(restful.Resource):

        def get(self, name):
            query_finder = default_query_finder()
            query = getattr(query_finder, name) or flask.abort(404)
            request = flask.request
            return query.search()

    api.add_resource(QueryResource, '/api/v1/q/<name>.json')

    api.representations.update({
        'application/json': custom_json_output
    })
