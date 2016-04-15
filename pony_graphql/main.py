# auto generation

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList
from graphql.core.type.scalars import GraphQLString, GraphQLInt
from graphql.core.type.schema import GraphQLSchema
from graphql.core.type import GraphQLID, GraphQLInputObjectType, \
    GraphQLInputObjectField
    
from graphql.core.type.schema import GraphQLSchema

from _types import SetType

def generate_schema(db):
    # types = []
    # for name, val in namespace.items():
    #     if isinstance(val, Entity):
    #         t = EntityType(name, val)
    #         types.append(t)
    # result = {}
    # for t in types:
    #     t.process(types=result)
    # return result
    
    entities = {k: v for k, v in db.__dict__.items()
        if isinstance(v, type)
        if issubclass(v, db.Entity)
        if v is not db.Entity
    }
    
    result = {}
    
    for name, entity in entities.items():
        typ = SetType(entity, result)
        result[name] = typ.get_graphql_type()
    
    print('schema: ', result)
    
    root = GraphQLObjectType(
        name='Query',
        fields=result
    )

    return GraphQLSchema(query=root)

