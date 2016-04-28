
from pony.orm import *
from pony.orm import core

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList, GraphQLInputObjectType, GraphQLInputObjectField, GraphQLInputObjectField
from graphql.core.type.scalars import GraphQLString, GraphQLInt, GraphQLBoolean, GraphQLScalarType
from graphql.core.language.ast import StringValue
from graphql.core.type.schema import GraphQLSchema


import inspect
from collections import namedtuple, OrderedDict
import json

from singledispatch import singledispatch

from mutations import EntityMutation, CreateEntityMutation, DeleteEntityMutation, \
        UpdateEntityMutation

from .util import ClassAttr, as_object

# TODO metaclass instead of decorator ?


#
# TODO cache python types also
#

def generate_schema(db):  
    _types = {}
    query = Query.from_db(db, _types)
    mut = Mutation.from_db(db, _types)
    return GraphQLSchema(query=query.as_graphql(), mutation=mut.as_graphql())


class Type(object):
    field_types = None

    def __init__(self,  types_dict):
        self.types_dict = types_dict
    
    def get_child_type(self, field_name):
        # disable adding children tree into the query ast
        return None
        
    add_to_ast = True
        
    
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
            return EntityConnectionType
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

    instance = None


class CustomType(Type):
    pass


class Query(Type):

    instance = None

    @classmethod
    def from_db(cls, db, types_dict):
        qu = cls.instance = cls(types_dict)
        qu.field_types = {}
        for name, entity in db.entities.items():
            typ = EntityConnectionType(entity, types_dict)
            qu.field_types[typ.name] = typ.make_field()
        return qu

    def as_graphql(self):
        return GraphQLObjectType(name=self.name, fields=self.field_types)


class Mutation(Type):

    instance = None
    
    @classmethod
    def from_db(cls, db, types_dict):
        mut = cls.instance = cls(types_dict)
        mut.field_types = {}
        for name, entity in db.entities.items():
            typ = EntityType(entity, types_dict)
            mut.field_types.update(typ.make_mutations())
        if getattr(db, 'mutations', None):
            mut.field_types.update(db.mutations)
        return mut
    
    def as_graphql(self):
        return GraphQLObjectType(self.name, fields=self.field_types)


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
    
    def get_child_type(self, field_name):
        ret = self.field_types.get(field_name)
        assert ret, field_name
        return ret
    
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
        self.field_types = dict(self.get_field_types())
        def get_fields():
            return {
                name: typ.make_field()
                for name, typ in self.field_types.items()
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

    def get_order_by(self):
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
    
    def get_query(self, obj, order_by=None, **kwargs):
        if hasattr(self, 'attr'):
            # TODO attr -> _attr_ or isinstance(self, Attr)
            query = getattr(obj, self.attr.name).select()
        else:
            query = select(o for o in self.entity)
        if order_by is None:
            order_by = self.get_order_by()
        return query.order_by(order_by)
    
    def __call__(self, obj, kwargs, info):
        query = self.get_query(obj, **kwargs)
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
        })
        self.types_dict[self.name] = typ
        return typ


class EntityConnectionType(EntitySetType):
    
    @property
    def node_type(self):
        return EntityType.as_graphql(self)
    
    def get_edge_type(self):
        entity_name = super(EntitySetType, self).name
        name = "%sEdge" % entity_name
        if name in self.types_dict:
            return self.types_dict[name]
        edge_type = GraphQLObjectType(name, {
            'node': GraphQLField(self.node_type),
            'cursor': GraphQLField(GraphQLNonNull(GraphQLString))
        })
        self.types_dict[name] = edge_type
        return edge_type

    # FIXME
    def make_field_types(self):
        if self.field_types is None:
            self.field_types = dict(self.get_field_types())

    # FIXME
    # @property
    # def name(self):
    #     entity_name = super(EntityConnectionType, self).name
    #     return "%sConnection" % entity_name

    def get_page_info_type(self):
        return PageInfoType(self.types_dict).as_graphql()

    def as_graphql(self):
        entity_name = super(EntityConnectionType, self).name
        name = "%sConnection" % entity_name
        if name in self.types_dict:
            return self.types_dict[name]
        connection_type = GraphQLObjectType(name, {
            'pageInfo': GraphQLField(self.get_page_info_type()),
            'edges': GraphQLField(
                GraphQLList(self.get_edge_type()),
            ),
            'items': GraphQLField(
                GraphQLList(self.node_type),
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
    
    def get_child_type(self, field_name):
        if field_name == 'pageInfo':
            return None
        if field_name in [
            'items', 'edges', 'node'
        ]:
            return self
        self.make_field_types()
        return EntitySetType.get_child_type(self, field_name)
    
    def get_pony_chain(self, chain):
        obj = self
        seen = {obj}
        for item in chain:
            obj = obj.get_child_type(item)
            if obj is not None and obj not in seen:
                yield item
                seen.add(obj)
            elif obj is None:
                break
            
        
    
    def __call__(self, obj, kwargs, info):
        # ast - ?
        from .ast_aware import AstTraverser
        import ipdb
        with ipdb.launch_ipdb_on_exception():
            tra = AstTraverser(info)
            pony = []
            for chain in tra:
                pony_ch = list(self.get_pony_chain(chain))
                pony.append(pony_ch)
            print('Pony AST: %s' % pony)
            return
        query = self.get_query(obj, **kwargs)
        page = self.paginate_query(query, **kwargs)
        edges = []
        for index, obj in enumerate(page):
            edges.append(as_object({
                'node': obj,
                'cursor': str(obj.id),
            }))
        
        get_id = lambda index: int(edges[index].cursor)
        has_next = edges and query.filter(lambda e: e.id > get_id(-1)).exists()
        has_prev = edges and query.filter(lambda e: e.id < get_id(0)).exists()
        
        return as_object({
            'pageInfo': as_object({
                'hasNextPage': has_next,
                'hasPreviousPage': has_prev,
            }),
            'edges': edges,
            'items': lambda: [e.node for e in edges],
        })
    
    def paginate_query(self, query, **kwargs):
        if 'before' in kwargs or 'last' in kwargs:
            cursor = kwargs.get('before')
            limit = kwargs.get('last')
            filter = lambda e: e.id < cursor
        else:
            filter = lambda e: e.id > cursor
            cursor = kwargs.get('after')
            limit = kwargs.get('first')

        if cursor is not None:
            cursor = int(cursor)
            # TODO only id is supported
            query = query.filter(filter)
        if limit is not None:
            query = query.limit(limit)
        return query
    
    def get_query(self, obj, order_by=None, **kwargs):
        # TODO forbid presence of both before and after in kwargs
        order_by = order_by or self.get_order_by()
        if 'before' in kwargs or 'last' in kwargs:
            order_by = order_by.desc()
        return EntitySetType.get_query(self, obj, order_by=order_by, **kwargs)        


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

from datetime import datetime

@Type.register(datetime)
class Datetime(Type):
    def parse_literal(self, ast):
        if isinstance(ast, StringValue):
            return ast.value
        return None

    from .util import parse_datetime as parse_value
    
    def serialize(self, dt):
        return dt.isoformat()

    def as_graphql(self):
        if self.name in self.types_dict:
            return self.types_dict[self.name]
        ret = GraphQLScalarType(
            name=self.name,
            description='The `Datetime` scalar type',
            serialize=self.serialize,
            parse_value=self.parse_value,
            parse_literal=self.parse_literal
        )
        self.types_dict[self.name] = ret
        return ret

from decimal import Decimal

@Type.register(Decimal)
class Decimal(Type):
    def parse_literal(self, ast):
        if isinstance(ast, StringValue):
            return ast.value
        return None

    def as_graphql(self):
        if self.name in self.types_dict:
            return self.types_dict[self.name]
        ret = GraphQLScalarType(
            name=self.name,
            description='The `Datetime` scalar type',
            serialize=str,
            parse_value=Decimal,
            parse_literal=self.parse_literal
        )
        self.types_dict[self.name] = ret
        return ret
        
