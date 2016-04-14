
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

    # field_handlers = {
    # #   py_type: klass
    # }

    def as_connection(self):
        ''

    

    # @property
    # def name(self):
    #     return self.__class__.__name__

    # getters = {'id': 'get_by_id'}

    def __init__(self, name, entity, query=None):
        self.name = name
        self.entity = entity
        
        

    # def resolve(parent, )

    
        
    def fetch(self, query):
        return self.entity._find_one_(query)


    def __call__(self, obj, args, info):
        ipdb.set_trace()
        return SetObject(query)

    def _make_fields(self, types):
        for attr in self.entity._attrs_:
            FieldType = Attr.py_type_handler(attr.py_type)
            field = FieldType(attr)
            yield attr.name, field.to_graphql(types)



    def to_graphql(self, types=0):
        fields = self._make_fields(types)
        object_type = GraphQLObjectType(
            name=self.name,
            fields=dict(fields),
            )
        return GraphQLField(object_type, resolver=self)


class SetResolver(object):
    
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
    
    def to_graphql(self, types):
        return GraphQLField(GraphQLInt)


# @Attr.register(str)
class StrType(Attr):
    
    def to_graphql(self, types):
        return GraphQLField(GraphQLString)
        
        


'''
Introspection | Fetching
'''

