# auto generation

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList
from graphql.core.type.scalars import GraphQLString, GraphQLInt
from graphql.core.type.schema import GraphQLSchema
from graphql.core.type import GraphQLID, GraphQLInputObjectType, \
    GraphQLInputObjectField
    
from graphql.core.type.schema import GraphQLSchema

# from _types import EntityType, EntitySetType, EntityConnectionType
from ._types import generate_schema