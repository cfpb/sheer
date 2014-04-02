from flask.ext import restful


def add_to_sheer(app):
    api = restful.Api(app)

    class HelloWorld(restful.Resource):
        def get(self):
            return {'hello':'world'}

    api.add_resource(HelloWorld, '/api/v1/')
