from functools import wraps
from graphql.core.type import (
    GraphQLArgument,
    GraphQLNonNull,
    GraphQLID,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLString,
    GraphQLBoolean,
    GraphQLObjectType,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
)

from pony import orm

def not_implemented(*args, **kw):
    raise NotImplementedError


class dict_as_obj(object):
    
    def __init__(self, d):
        self.__dict__ = d
        
    def __repr__(self):
        return repr(self.__dict__)



class MutationMarker(object):
    
    class decorator(dict):
        def __call__(self, func=None, **kwargs):
            if func is None:
                self.update(kwargs)
                if 'name' in kwargs:
                    self['__named__'] = True
                return self
            if not self.get('__named__'):
                self['name'] = func.__name__
            func.mutation = self
            return func 
    
    def __init__(self, decorator=None):
        if decorator:
            self.decorator = decorator
    
    def __get__(self, instance, owner):
        return self.decorator({
            'type': owner,
            'name': owner.name,
        })


class ClassAttrRef(object):
    def __init__(self, attr_name):
        self.attr_name = attr_name
    
    def __get__(self, isinstance, owner):
        return getattr(owner, self.attr_name)


class RelayMutationType(object):

    input_fields_getter = lambda *args: {}
    output_fields_getter = lambda *args: {}
    mutate_func = not_implemented

    name = ClassAttrRef('__name__')
    
    mark = MutationMarker()
    
    # This attribute allows declared classes to be collected as mutations
    mutation = ClassAttrRef('mark')
    
    def __init__(self, mutate=None, get_input_fields=None, get_output_fields=None,
                 **kwargs):
        if mutate is not None:
            self.mutate_func = mutate
        if get_input_fields is not None:
            self.input_fields_getter = get_input_fields
        if get_output_fields is not None:
            self.output_fields_getter = get_output_fields
        self.__dict__.update(kwargs)

    @property
    def get_input_fields(self):
        return self.input_fields_getter
        
    @property
    def get_output_fields(self):
        return self.output_fields_getter

    @property
    def mutate(self):
        return self.mutate_func

    def __call__(self, obj, args, info):
        params = args.get('input')
        clientMutationId = params.pop('clientMutationId', None)
        result = self.mutate(**params)
        result = self.transform_result(result)
        if clientMutationId is not None:
            result.clientMutationId = clientMutationId
        return result
        
    def transform_result(self, result):
        if isinstance(result, dict):
            return dict_as_obj(result)
        return result

    def make_field(self):
        output_fields = self.get_output_fields()
        output_fields.update({
            'clientMutationId': GraphQLField(GraphQLString)
        })
        output_type = GraphQLObjectType(
            self.name + 'Payload',
            fields=output_fields)
        input_fields = self.get_input_fields()
        input_fields.update({
            'clientMutationId': GraphQLInputObjectField(GraphQLString)
        })
        input_arg = GraphQLArgument(GraphQLNonNull(GraphQLInputObjectType(
            name=self.name + 'Input',
            fields=input_fields)))
        return GraphQLField(
            output_type,
            args = {
                'input': input_arg,
            },
            resolver=self
        )

class PonyMutation(RelayMutationType):

    def mutate(self, **kwargs):
        ret = self.mutate_func(**kwargs)
        orm.flush()
        return ret
        


class BooleanResultMutation(PonyMutation):
    def get_output_fields(self):
        return {
            'ok': GraphQLField(GraphQLBoolean)
        }
    
    def transform_result(self, result):
        result = {'ok': bool(result)}
        return RelayMutationType.transform_result(self, result)


class EntityMutation(PonyMutation):

    @classmethod
    def from_entity_type(cls, entity_type, **kwargs):
        mut = cls(**kwargs)
        mut.entity_type = entity_type
        return mut

    @property
    def mutate(self):
        entity = self.entity_type.entity
        
        @wraps(self.mutate_func)
        def wrapper(get, **kwargs):
            obj = entity._find_one_(get)
            self.mutate_func(obj, **kwargs)
            orm.flush()
            return obj
        
        return wrapper

    def transform_result(self, result):
        if isinstance(result, self.entity_type.entity):
            result = {'instance': result}
        return RelayMutationType.transform_result(self, result)

    def _get_entity_inputs(self):
        result = {}
        for key, typ in self.entity_type.get_field_types():
            result[key] = GraphQLInputObjectField(typ.as_input())
        return result

    def get_input_fields(self):
        GetEntity = GraphQLInputObjectType(
            name=self.name + 'Get',
            fields=self._get_entity_inputs())
        return {
            'get': GraphQLInputObjectField(GetEntity),
        }

    def get_output_fields(self):
        return {
            'instance': self.entity_type.make_field(),
        }


class UpdateEntityMutation(EntityMutation):

    def get_input_fields(self):
        inputs = EntityMutation.get_input_fields(self)
        inputs.update(
            self._get_entity_inputs()
        )
        return inputs


class CreateEntityMutation(EntityMutation):

    mutate = PonyMutation.mutate
    
    def get_input_fields(self):
        return self._get_entity_inputs()


class DeleteEntityMutation(BooleanResultMutation, EntityMutation):
    pass


class DbMutation(BooleanResultMutation):
    def __init__(self, db):
        self.db = db

    def mutate(self):
        raise NotImplementedError

    def register(self):
        mutations = self.db.__dict__.setdefault('mutations', {})
        mutations.update({
            self.name: self.make_field()
        })
