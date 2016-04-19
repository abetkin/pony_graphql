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

import ipdb

def not_implemented(*args, **kw):
    raise NotImplementedError


class dict_as_obj(object):
    
    def __init__(self, d):
        self.__dict__ = d
        
    def __repr__(self):
        return repr(self.__dict__)



class RelayMutationType(object):

    input_fields_getter = None
    output_fields_getter = None
    mutate_func = None
    
    def __init__(self, mutate=None, name=None,
                 get_input_fields=None, get_output_fields=None,
                 **kwargs):
        if mutate is not None:
            self.mutate_func = mutate
        if get_input_fields is not None:
            self.input_fields_getter = get_input_fields
        if get_output_fields is not None:
            self.output_fields_getter = get_output_fields
        if name is not None:
            self.name = name
        self.__dict__.update(kwargs)

    @property
    def get_input_fields(self):
        if self.input_fields_getter:
            return self.input_fields_getter
        return not_implemented
        
    @property
    def get_output_fields(self):
        if self.output_fields_getter:
            return self.output_fields_getter
        return not_implemented

    @property
    def mutate(self):
        if self.mutate_func is not None:
            return self.mutate_func
        return not_implemented

    def __call__(self, obj, args, info):
        params = args.get('input')
        clientMutationId = params.pop('clientMutationId')
        result = self.mutate_func(**params)
        result = self.transform_result(result)
        result.clientMutationId = clientMutationId
        return result
        
    def transform_result(self, result):
        if isinstance(result, dict):
            return dict_as_obj(result)
        return result

    def make_field(self):
        output_fields = self.get_output_fields()
        output_fields.update({
            'clientMutationId': GraphQLField(GraphQLNonNull(GraphQLString))
        })
        output_type = GraphQLObjectType(
            self.name + 'Payload',
            fields=output_fields)
        input_fields = self.get_input_fields()
        input_fields.update({
            'clientMutationId':
                GraphQLInputObjectField(GraphQLNonNull(GraphQLString))
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


class EntityMutation(RelayMutationType):

    @classmethod
    def from_entity_type(cls, entity_type, **kwargs):
        mut = cls(**kwargs)
        mut.entity_type = entity_type
        return mut

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
        if self.input_fields_getter:
            return self.input_fields_getter()
        GetEntity = GraphQLInputObjectType(
            name=self.name + 'Get',
            fields=self._get_entity_inputs())
        return {
            'get': GraphQLInputObjectField(GetEntity),
        }

    def get_output_fields(self):
        if self.output_fields_getter:
            return self.output_fields_getter()
        print('et', self.entity_type)
        return {
            'instance': self.entity_type.make_field(),
        }


class UpdateEntityMutation(EntityMutation):

    def get_input_fields(self):
        fields = EntityMutation.get_input_fields(self)
        fields.update(
            self._get_entity_inputs()
        )
        return fields


class CreateEntityMutation(EntityMutation):
    
    def get_input_fields(self):
        return self._get_entity_inputs()


class DeleteEntityMutation(EntityMutation):

    def get_output_fields(self):
        return {
            'ok': GraphQLField(GraphQLBoolean)
        }
