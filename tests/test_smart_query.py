import unittest

import sys, os

from cached_property import cached_property

import pony
from pony import orm

from graphql.core.language.parser import parse


from pony_graphql.main import generate_schema

from graphql.core.execution.executor import Executor
from graphql.core.execution.middlewares.sync import SynchronousExecutionMiddleware

import ipdb

class SmartQueryTest(unittest.TestCase):
    
    db_name = 'sqtest.db'


    @cached_property
    def schema(self):
        return generate_schema(self.db)

    def setUp(self):
        db_path = os.path.dirname(__file__)
        db_path = os.path.join(db_path, self.db_name)
        try:
            os.remove(db_path)
        except OSError:
            pass
        db = self.db = orm.Database('sqlite', self.db_name, create_db=True)
        
        class Genre(db.Entity):
            name = orm.Required(str)
            artists = orm.Set('Artist')
        
        class Artist(db.Entity):
            name = orm.Required(str)
            age = orm.Optional(int)
            genres = orm.Set(Genre)

        
        db.generate_mapping(check_tables=True, create_tables=True)
    
        with orm.db_session:
            pop = Genre(name='pop')
            rock = Genre(name='rock')
            a = Artist(name='Sia', age=40, genres=[pop, rock])
            a = Artist(name='Umka', age=55, genres=[rock, pop])
    
        pony.options.INNER_JOIN_SYNTAX = True
    

    
    query = '''
    {
        Artist (first: 5, ifs: "x.age < 100") {
            items {
                age
                genres {
                    items { name }
                    
                }
            }
        }
    }
    '''
    # edges { node { name }}
    
    class Middleware(object):
        @staticmethod
        def run_resolve_fn(resolver, original_resolver):
            import ipdb
            with ipdb.launch_ipdb_on_exception(), orm.db_session:
                return SynchronousExecutionMiddleware.run_resolve_fn(resolver, original_resolver)

        @staticmethod
        def execution_result(executor):
            with orm.db_session:
                return SynchronousExecutionMiddleware.execution_result(executor)
    
    
    @cached_property
    def executor(self):
        return Executor([self.Middleware()])

    def execute(self, schema, root, ast, operation_name='', args=None):
        return self.executor.execute(
            schema, ast, root, args, operation_name, validate_ast=False
        )
    
    
    @orm.db_session
    def test(self):
        # import ipdb
        # with ipdb.launch_ipdb_on_exception():
            
        ast = parse(self.query)
        result = self.execute(self.schema, None, ast)
        print(result.data)
        self.assertFalse(result.errors)
            
