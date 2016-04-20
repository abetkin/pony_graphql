
from pony.orm import *
from pony.orm import core

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList, GraphQLInputObjectType, GraphQLInputObjectField, GraphQLInputObjectField
from graphql.core.type.scalars import GraphQLString, GraphQLInt, GraphQLBoolean
from graphql.core.type.schema import GraphQLSchema


import inspect

from singledispatch import singledispatch

from mutations import EntityMutation, CreateEntityMutation, DeleteEntityMutation, \
        UpdateEntityMutation



# TODO metaclass instead of decorator ?

class Type(object):

    def __init__(self,  types_dict):
        self.types_dict = types_dict
    
    @classmethod
    def from_attr(cls, attr, types_dict):
        instance = cls(types_dict)
        instance.attr = attr
        return instance
        
    def as_graphql(self):
        raise NotImplementedError
        
    def as_input(self):
        return self.as_graphql()

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
        Type.__init__(self, types_dict)
        self.entity = entity


    @classmethod
    def from_attr(cls, attr, types_dict):
        instance = cls(attr.py_type, types_dict)
        instance.attr = attr
        return instance
    
    def get_field_types(self):
        for attr in self.entity._attrs_:
            FieldType = self.dispatch_attr(attr)
            field_type = FieldType.from_attr(attr, self.types_dict)
            yield attr.name, field_type
    
    @CreateEntityMutation.mark
    def create(self, **kwargs):
        return self.entity(**kwargs)
        
    @UpdateEntityMutation.mark
    def update(self, obj, **kwargs):
        for key, val in kwargs.items():
            setattr(obj, key, val)
    
    @DeleteEntityMutation.mark
    def delete(self, obj):
        obj.delete()
        return True

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
    
        
    def _collect_mutations(self):
        is_mutation = lambda value: hasattr(value, 'mutation') and callable(value)
        for name, val in self.__class__.__dict__.items():
            if is_mutation(val):
                config = dict(val.mutation)
                mutate = getattr(self, name)
                if inspect.ismethod(mutate):
                    config['mutate'] = mutate
                yield config
        for name, val in self.entity.__dict__.items():
            if is_mutation(val):
                config = dict(val.mutation)
                mutate = getattr(self.entity, name)
                if inspect.ismethod(mutate):
                    config['mutate'] = mutate
                yield config     
    
    def make_mutations(self):
        fields = {}
        for config in self._collect_mutations():
            kw = dict(config)
            name = kw['name']
            kw['name'] = ''.join((name[0].upper(), name[1:]))
            kw['name'] = ''.join((kw['name'], self.name))
            mut = kw['type'].from_entity_type(self, **kw)
            mutation_name = ''.join((name, self.name))
            fields[mutation_name] = mut.make_field()
        return fields
    
    def as_input(self):
        PkType = Type.dispatch(self.entity._pk_.py_type)
        typ = PkType(self.types_dict)
        return typ.as_input()


class EntitySetType(EntityType):

    def make_field(self, resolver=None):
        typ = self.as_graphql()
        return GraphQLField(typ, resolver=self)

    def as_input(self):
        entity_input = EntityType.as_input(self)
        return GraphQLList(entity_input)

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

@Type.register(bool)
class BooleanType(Type):
    
    def as_graphql(self):
        return GraphQLBoolean
        

class ConnectionField(object):
    1



