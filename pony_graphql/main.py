# auto generation

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList
from graphql.core.type.scalars import GraphQLString, GraphQLInt
from graphql.core.type.schema import GraphQLSchema
from graphql.core.type import GraphQLID, GraphQLInputObjectType, \
    GraphQLInputObjectField
    
from graphql.core.type.schema import GraphQLSchema

from _types import EntityType, EntitySetType, EntityConnectionType


def generate_schema(db):  
    _types = {}
    fields = {}
    mutations = {}
    for name, entity in db.entities.items():
        typ = EntitySetType(entity, _types)
        fields[name] = typ.make_field()

    for name, entity in db.entities.items():
        typ = EntityConnectionType(entity, _types)
        fields['%sConnection' % typ.name] = typ.make_field()

    for name, entity in db.entities.items():
        typ = EntityType(entity, _types)
        mutations.update(typ.make_mutations())

    if getattr(db, 'mutations', None):
        mutations.update(db.mutations)

    query = GraphQLObjectType(name='Query', fields=fields)
    mutation = GraphQLObjectType('Mutation', fields=mutations)
    return GraphQLSchema(query=query, mutation=mutation)
