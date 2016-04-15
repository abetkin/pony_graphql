
from pony.orm import *
from pony.orm import core

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList
from graphql.core.type.scalars import GraphQLString, GraphQLInt
from graphql.core.type.schema import GraphQLSchema


import ipdb

# from singledispatch import singledispatch



class Attr(object):

    @classmethod
    def get_handlers(cls):
        return {
            int: IntType,
            str: StrType,
        }

    @classmethod
    # @singledispatch
    def py_type_handler(cls, py_type):
        return cls.get_handlers()[py_type]
        # then iterate
    
    # def default_attr_handler(attr):
    #     if isinstance(attr, Set):
    #         return SetAttrType(attr)
    #     raise NotImplementedError

    

    @classmethod
    def register(cls, py_type):
        '''
        Register attribute handler
        '''
        def decorate(klass):
            cls.py_type_handler.register(py_type, lambda: klass)
            return klass
        return decorate


    def __init__(self, attr):
        self.attr = attr
    
    def resolve(self, obj):
        return getattr(obj, attr.name)


class SetType(object):
    '''
    Actually, queryset
    '''

    def as_connection(self):
        ''

    def __init__(self, entity, schema):
        # self.name = name
        self.entity = entity
        self.schema = schema

    def __call__(self, obj, args, info):
        if 'obj is root':
            qs = select(o for o in self.entity)[:]
            print('qs = ', qs)
            return qs

    @property
    def name(self):
        return '%sSet' % self.entity.__name__

    def process(self):
        1

    # make
    def get_graphql_type(self):
        if self.name in self.schema:
            return self.schema[self.name]
        entity_type = EntityType(self.entity, self.schema).get_graphql_type()
        list_type = GraphQLList(entity_type)
        field_type = GraphQLField(list_type, resolver=self)
        self.schema[self.name] = field_type
        return field_type


class EntityType(object):

    def __init__(self, entity, schema):
        self.entity = entity
        self.schema = schema

    def _make_fields(self):
        for attr in self.entity._attrs_:
            FieldType = Attr.py_type_handler(attr.py_type)
            field = FieldType(attr)
            yield attr.name, field.get_graphql_type()

    @property
    def name(self):
        return self.entity.__name__

    def get_graphql_type(self):
        if self.name in self.schema:
            return self.schema[self.name]
        fields = self._make_fields()
        object_type = GraphQLObjectType(
            name=self.name,
            fields=dict(fields),
            )
        self.schema[self.name] = object_type
        return object_type
        
        
        


class SetObject(object):
    
    def __init__(self, _set):
        entity = 2
        self.query = 1
    
    

    
    

class SetAttrType(SetType):
    pass

# class ResolvedSet(object):
#     def __init__(self):
#         1

#     def first(self):
#         1




# @Attr.register(int)
class IntType(Attr):
    
    def get_graphql_type(self):
        return GraphQLField(GraphQLInt)


# @Attr.register(str)
class StrType(Attr):
    
    def get_graphql_type(self):
        return GraphQLField(GraphQLString)
        
        


'''
Introspection | Fetching
'''

