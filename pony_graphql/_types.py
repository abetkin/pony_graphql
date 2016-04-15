
from pony.orm import *
from pony.orm import core

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList
from graphql.core.type.scalars import GraphQLString, GraphQLInt
from graphql.core.type.schema import GraphQLSchema


import ipdb, IPython

from singledispatch import singledispatch


class AttrField(object):

    def _dispatcher(py_type):
        return AttrField
    
    _dispatcher = singledispatch(_dispatcher)

    @classmethod
    def dispatch(cls, py_type):
        '''
        Dispatch to the handler class
        '''
        return cls._dispatcher.dispatch(py_type)

    @classmethod
    def register(cls, py_type):
        '''
        Register class as attribute handler
        '''
        def decorate(klass):
            cls._dispatcher.register(py_type, klass)
            return klass
        return decorate

    def __init__(self, attr, types_dict):
        self.attr = attr
        self.types_dict = types_dict
    


class SetField(object):
    '''
    Queryset for an entity
    '''

    def __init__(self, entity, types_dict):
        self.entity = entity
        self.types_dict = types_dict

    def as_graphql(self):
        entity_type = EntityType(self.entity, self.types_dict).as_graphql()
        list_type = GraphQLList(entity_type)
        return GraphQLField(list_type, resolver=self)


class EntityType(object):

    def __init__(self, entity, types_dict):
        self.entity = entity
        self.types_dict = types_dict

    def get_fields(self):
        result = {}
        for attr in self.entity._attrs_:
            FieldType = AttrField.dispatch(attr.py_type)
            field = FieldType(attr, self.types_dict)
            result[attr.name] = field.as_graphql()
        return result

    @property
    def name(self):
        return self.entity.__name__

    def as_graphql(self):
        if self.name in self.types_dict:
            return self.types_dict[self.name]
        
        object_type = GraphQLObjectType(
            name=self.name,
            fields=self.get_fields,
            )
        self.types_dict[self.name] = object_type
        return object_type
        
        

@AttrField.register(core.Entity)
class AttrSetField(SetField, AttrField):
    
    def __init__(self, attr, types_dict):
        AttrField.__init__(self, attr, types_dict)
        entity = attr.py_type
        SetField.__init__(self, entity, types_dict)
    
    def __call__(self, obj, args, info):
        name = self.attr.name
        return list(getattr(obj, name))
    

class RootEntitySetField(SetField):

    def __call__(self, obj, args, info):
        return select(o for o in self.entity)[:]


@AttrField.register(int)
class IntType(AttrField):
    
    def as_graphql(self):
        return GraphQLField(GraphQLInt)


@AttrField.register(str)
class StrType(AttrField):
    
    def as_graphql(self):
        return GraphQLField(GraphQLString)
        
        

class ConnectionField(object):
    1

