



from flask import Flask
from flask.ext.cors import CORS
from flask_graphql import GraphQL

from schema import schema, orm

app = Flask(__name__, static_url_path='/static/')
app.debug = True


from graphql.core.execution import Executor, SynchronousExecutionMiddleware

class PonyMiddleware(object):
    @staticmethod
    def run_resolve_fn(resolver, original_resolver):
        import ipdb
        with ipdb.launch_ipdb_on_exception(), orm.db_session:
            return SynchronousExecutionMiddleware.run_resolve_fn(resolver, original_resolver)

    @staticmethod
    def execution_result(executor):
        with orm.db_session:
            return SynchronousExecutionMiddleware.execution_result(executor)

executor = Executor([PonyMiddleware()])
graphql = GraphQL(app, schema=schema, executor=executor)

CORS(app)





with orm.db_session:
    app.run()

