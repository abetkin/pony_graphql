# auto generation

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList
from graphql.core.type.scalars import GraphQLString, GraphQLInt
from graphql.core.type.schema import GraphQLSchema
from graphql.core.type import GraphQLID, GraphQLInputObjectType, \
    GraphQLInputObjectField
    
from graphql.core.type.schema import GraphQLSchema

from _types import RootEntitySetField

def generate_schema(db):
    entities = {k: v for k, v in db.__dict__.items()
        if isinstance(v, type)
        if issubclass(v, db.Entity)
        if v is not db.Entity
    }
    
    _types = {}
    fields = {
        name: RootEntitySetField(entity, _types).as_graphql()
        for name, entity in entities.items()
    }

    root = GraphQLObjectType(
        name='Query',
        fields=fields
    )

    return GraphQLSchema(query=root)

