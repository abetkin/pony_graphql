
from pony.orm import *
from pony.orm import core

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList, GraphQLInputObjectType, GraphQLInputObjectField, GraphQLInputObjectField
from graphql.core.type.scalars import GraphQLString, GraphQLInt, GraphQLBoolean
from graphql.core.type.schema import GraphQLSchema


import inspect
from collections import namedtuple, OrderedDict
import json

from singledispatch import singledispatch

from mutations import EntityMutation, CreateEntityMutation, DeleteEntityMutation, \
        UpdateEntityMutation

from .util import ClassAttr, as_object

# TODO metaclass instead of decorator ?

class Type(object):

    def __init__(self,  types_dict):
        self.types_dict = types_dict
        
    name = ClassAttr('__name__')
    
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
            # TODO connection!
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
            # TODO merge into dispatch_attr
    
    @CreateEntityMutation.mark
    def create(self, **kwargs):
        return self.entity(**kwargs)
        
    @UpdateEntityMutation.mark
    def update(self, obj, **kwargs):
        for key, val in kwargs.items():
            py_type = getattr(self.entity, key).py_type
            if issubclass(py_type, core.Entity):
                # have to do this because of Pony bug
                from collections import Sequence
                if isinstance(val, Sequence):
                    val = [py_type[item] for item in val]
                else:
                    val = py_type[val]
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
        is_mutation = lambda value: hasattr(value, '__mutation__')
        for name, val in self.__class__.__dict__.items():
            if is_mutation(val):
                config = dict(val.__mutation__)
                mutate = getattr(self, name)
                if inspect.ismethod(mutate):
                    config['mutate'] = mutate
                yield config
        for name, val in self.entity.__dict__.items():
            if is_mutation(val):
                config = dict(val.__mutation__)
                mutate = getattr(self.entity, name)
                if inspect.ismethod(mutate):
                    config['mutate'] = mutate
                yield config     
    
    def make_mutations(self):
        fields = {}
        for config in self._collect_mutations():
            name = config['name']
            config['name'] = ''.join((name[0].upper(), name[1:]))
            config['name'] = ''.join((config['name'], self.name))
            mut = config['type'].from_entity_type(self, **config)
            mutation_name = ''.join((name, self.name))
            fields[mutation_name] = mut.make_field()
        return fields
    
    def as_input(self):
        PkType = Type.dispatch(self.entity._pk_.py_type)
        typ = PkType(self.types_dict)
        return typ.as_input()
     
    # TODO maybe rename as_graphql 
     

class EntitySetType(EntityType):

    @property
    def order_by(self):
        return self.entity._pk_

    arguments = {}

    def make_field(self, resolver=None):
        typ = self.as_graphql()
        return GraphQLField(typ, args=self.arguments, resolver=self)

    def as_input(self):
        entity_input = EntityType.as_input(self)
        return GraphQLList(entity_input)

    def as_graphql(self):
        entity_type = EntityType.as_graphql(self)
        return GraphQLList(entity_type)
    
    def get_query(self, **kwargs):
        if hasattr(self, 'attr'):
            # TODO attr -> _attr_ or isinstance(self, Attr)
            query = getattr(obj, self.attr.name).select()
        else:
            query = select(o for o in self.entity)
        return query.order_by(self.order_by)
    
    def __call__(self, obj, kwargs, info):
        query = self.get_query(**kwargs)
        return list(query)
        


class PageInfoType(Type):

    def as_graphql(self):
        if self.name in self.types_dict:
            return self.types_dict[self.name]
        typ = GraphQLObjectType(self.name, {
            'hasNextPage': GraphQLField(
                GraphQLNonNull(GraphQLBoolean),
            ),
            'hasPreviousPage': GraphQLField(
                GraphQLNonNull(GraphQLBoolean),
            ),
            'startCursor': GraphQLField(
                GraphQLString,
            ),
            'endCursor': GraphQLField(
                GraphQLString,
            ),
        })
        self.types_dict[self.name] = typ
        return typ


class EntityConnectionType(EntitySetType):
    
    def get_edge_type(self):
        entity_name = super(EntitySetType, self).name
        name = "%sEdge" % entity_name
        if name in self.types_dict:
            return self.types_dict[name]
        node_type = EntityType.as_graphql(self)
        edge_type = GraphQLObjectType(name, {
            'node': GraphQLField(node_type),
            'cursor': GraphQLField(GraphQLNonNull(GraphQLString))
        })
        self.types_dict[name] = edge_type
        return edge_type

    # FIXME
    # @property
    # def name(self):
    #     entity_name = super(EntityConnectionType, self).name
    #     return "%sConnection" % entity_name

    def as_graphql(self):
        entity_name = super(EntityConnectionType, self).name
        name = "%sConnection" % entity_name
        if name in self.types_dict:
            return self.types_dict[name]
        edge_type = self.get_edge_type()
        page_info_type = PageInfoType(self.types_dict).as_graphql()
        connection_type = GraphQLObjectType(name, {
            'pageInfo': GraphQLField(page_info_type),
            'edges': GraphQLField(
                GraphQLList(edge_type),
            )
        })
        self.types_dict[name] = connection_type
        return connection_type
    
    arguments = {
        'before': GraphQLArgument(GraphQLString),
        'after': GraphQLArgument(GraphQLString),
        'first': GraphQLArgument(GraphQLInt),
        'last': GraphQLArgument(GraphQLInt),
    }
    
    def __call__(self, obj, kwargs, info):
        query = self.get_query(**kwargs)
        def edges():
            for index, obj in enumerate(query):
                cursor = Cursor(**{
                    'order_by': self.order_by.name,
                    'id': obj.id,
                })
                yield as_object({
                    'node': obj,
                    'cursor': cursor.dumps(),
                })
        return as_object({
            'edges': list(edges())
        })
    
    
    # arg = CallableCollector()
    
    # @arg
    # def before(self, query, cursor):
    #     1
    
    # @arg
    # def after(self, query, cursor):
    #     1
    
    # @arg
    # def first(self, query, count):
    #     1
    
    # @arg
    # def last(self, query):
    #     1
    
    
    def get_query(self, **kwargs):
        # TODO forbid presence of both before and after in kwargs
        query = EntitySetType.get_query(self, **kwargs)
        filter = {}
        if 'after' in kwargs:
            cursor = kwargs['after']
            cursor = Cursor.loads(cursor)
            if cursor.order_by != self.order_by.name:
                assert 0
            # TODO only id is supported
            query = query.filter(lambda e: e.id > cursor.id)
        if 'first' in kwargs:
            query = query.limit(kwargs['first'])
        return query


    
class Cursor(namedtuple('CursorNT', ['id', 'order_by'])):

    def dumps(self):
        return ':'.join(map(str, self))
    
    @classmethod
    def loads(cls, string):
        id, order_by = string.split(':')
        id = int(id)
        return cls(id, order_by)



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



