
from pony.orm import *

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList
from graphql.core.type.scalars import GraphQLString, GraphQLInt
from graphql.core.type.schema import GraphQLSchema


from singledispatch import singledispatch

class EntityType:

    field_handlers = {
    #   py_type: klass
    }

    @singledispatch
    def _make_field():
        '''
        '''
        raise NotImplementedError

    @property
    def name(self):
        return self.__class__.__name__

    # getters = {'id': 'get_by_id'}

    def __init__(self, entity):
        self.entity = entity

    # def get_by_id(self, id):
    #     return self.entity.get(id=id)

    def _resolver(self, obj, args, info):
        kwargs = dict(args)
        return self.entity._find_one_(kwargs)

    # register like FuncCall



    def get_fields(self):
        1

    @classmethod
    def register_field_handler(cls, py_type):
        def decorate(klass):
            f = klass.somefunc
            cls._make_field.register(f)
        return decorate


    field_handler = register_field_handler

    def make(self):
        return GraphQLObjectType(
            name=self.name,
            fields=get_fields(),
            resolver=self.resolver
            )

    def fetch_data(self, query):
        'default: query = dict(args) from resolver'
        



@EntityType.field_handler(int, str)
def simple(obj, name):
    return getattr(obj.name)


class FieldType:
    def __init__(self, entity, attr):
        self.entity = entity
        self.attr = attr
    
    def get_value(self, data):
        '(parent) ?'
        return getattr(data, attr.name)


class IntType(FieldType):
    1


class SetType(FieldType):
    '''
    -> connection
    '''

    def add_me(self, types, name):
        1


'''
Introspection | Fetching
'''