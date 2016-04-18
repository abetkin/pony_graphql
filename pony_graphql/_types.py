
from pony.orm import *
from pony.orm import core

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList
from graphql.core.type.scalars import GraphQLString, GraphQLInt
from graphql.core.type.schema import GraphQLSchema


import ipdb, IPython

from singledispatch import singledispatch

from relay import RelayMutationType

# TODO metaclass instead of decorator ?

class Type(object):

    def __init__(self, py_type, types_dict):
        self.py_type = py_type
        self.types_dict = types_dict
    
    @classmethod
    def from_attr(cls, attr, types_dict):
        instance = cls(attr.py_type, types_dict)
        instance.attr = attr
        return instance
        
    def as_graphql(self):
        raise NotImplementedError

    def make_field(self, resolver=None):
        return GraphQLField(self.as_graphql())

    def _dispatcher(py_type):
        return CustomType

    _dispatcher = singledispatch(_dispatcher) 


    def dispatch_attr(cls, attr):
        if isinstance(attr, Set):
            return EntitySetType
        return cls.dispatch(attr.py_type)

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


class CustomType(Type):
    pass




# TODO filter: {}
#

# TODO tell executor about db_session





@Type.register(core.Entity)
class EntityType(Type):

    def __init__(self, entity, types_dict):
        Type.__init__(self, entity, types_dict)
        self.entity = entity

    mutations = []
    
    def mutation(f, _mutations=mutations):
        _mutations.append(f.__name__)
        return f
    
    def make_mutation(self, name, input_fields=None, output_fields=None):
        '%sInput' % name
        {
            key: GraphQLArgument(typ)
            for key, typ in self.get_field_types()
        }
        '%sPayload' % name
        def resolve():
            1
        {
            'instance': self.as_graphql.make_field(resolve)
        }
        
    # m = mutation(input, output)

    def get_field_types(self):
        for attr in self.entity._attrs_:
            FieldType = self.dispatch_attr(attr)
            field_type = FieldType.from_attr(attr, self.types_dict)
            yield attr.name, field_type
    
    @mutation
    def create(self, **kwargs):
        obj = self.entity(**kwargs)
        flush()
        return obj
        
    @mutation
    def update(self, get_kwargs, **kwargs):
        obj = self.entity._find_one_(**get_kwargs)
        obj.__dict__.update(kwargs)
        flush()
        return obj

    @property
    def name(self):
        return self.entity.__name__

    def as_graphql(self):
        if self.name in self.types_dict:
            return self.types_dict[self.name]
        def get_fields():
            return {
                name: typ.make_field()
                for name, typ in self.get_field_types()
            }
        object_type = GraphQLObjectType(
            name=self.name,
            fields=get_fields,
            )
        self.types_dict[self.name] = object_type
        return object_type
    
    del mutation


class EntitySetType(EntityType):

    def make_field(self, resolver=None):
        typ = self.as_graphql()
        return GraphQLField(typ, resolver=self)

    def as_graphql(self):
        entity_type = EntityType.as_graphql(self)
        return GraphQLList(entity_type)
        
    def __call__(self, obj, args, info):
        if hasattr(self, 'attr'):
            # TODO attr -> _attr_ or isinstance(self, Attr)
            value = getattr(obj, self.attr.name)
            return list(value)
        return select(o for o in self.entity)[:]
        
        

@Type.register(int)
class IntType(Type):
    
    def as_graphql(self):
        return GraphQLInt


@Type.register(str)
class StrType(Type):
    
    def as_graphql(self):
        return GraphQLString

        

class ConnectionField(object):
    1


class MutationField(object):
    '''
    create update delete
    '''
    
    def __init__(self, entity):
        1
        
        
class CreateUpdateEntityInput(Type):

    def get_input_fields(self):
        raise NotImplementedError

    def get_output_fields(self):
        raise NotImplementedError

    def as_graphql(self):
        RelayMutationType.build()