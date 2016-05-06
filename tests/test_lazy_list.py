from graphql.core.execution import execute
from graphql.core.language.parser import parse
from graphql.core.type import (GraphQLBoolean, GraphQLField,
                               GraphQLInterfaceType, GraphQLList,
                               GraphQLObjectType, GraphQLSchema, GraphQLString,
                               GraphQLUnionType)

from graphql.core.execution.executor import Executor
from graphql.core.execution.middlewares.sync import SynchronousExecutionMiddleware

from cached_property import cached_property

from pony import orm

import unittest


class mydict(object):
    def __init__(self, wrapped, log):
        self.wrapped = wrapped
        self.log = log

    def __getattr__(self, key):
        self.log('getattr %s' % key)
        return self.wrapped[key]

    def __repr__(self):
        return repr(self.wrapped)

class mylist(object):

    def __init__(self, wrapped, log):
        self.wrapped = wrapped
        self.log = log

    def __iter__(self):
        for i in self.wrapped:
            self.log('__iter__ %s' % i)
            yield i

    def __repr__(self):
        return repr(self.wrapped)


class Test(unittest.TestCase):
    # TODO -> __init__.py
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


        

    def log(self, item):
        logger = self.__dict__.setdefault('logger', [])
        logger.append(item)

    def setUp(self):
        ItemType = GraphQLObjectType(
            name='Item',
            fields={
                'name': GraphQLField(GraphQLString),
            },
        )

        items = GraphQLField(
            GraphQLList(ItemType),
            resolver=lambda *ar, **kw: self.items
        )

        ObjType = GraphQLObjectType(
            name='Obj',
            fields={
                'items': items,
            },
        )

        self.schema = GraphQLSchema(ObjType)

    @cached_property
    def items(self):
        return mylist([
            mydict({'name': 'A'}, self.log),
            mydict({'name': 'B'}, self.log),
        ], self.log)

    def resolve_list(self, obj, kwargs, info):
        return self.items
        # return lazy_list(self.items)

    query = '''
    {
        items {
            name
        }
    }
    '''

    def test(self):
        ast = parse(self.query)
        result = self.execute(self.schema, None, ast)
        self.assertFalse(result.errors)
        self.assertListEqual(self.logger, [
            "__iter__ {'name': 'A'}",
            'getattr name',
            "__iter__ {'name': 'B'}",
            'getattr name'
        ])