# auto generation

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList
from graphql.core.type.scalars import GraphQLString, GraphQLInt
from graphql.core.type.schema import GraphQLSchema
from graphql.core.type import GraphQLID, GraphQLInputObjectType, \
    GraphQLInputObjectField
    
from graphql.core.type.schema import GraphQLSchema

from _types import RootEntitySetField






# class AddPostMutation(RelayMutation):
#     name = 'AddPost'

#     def get_input_fields(self):
#         return {
#             'parent_id': GraphQLInputObjectField(GraphQLInt),
#             'title': GraphQLInputObjectField(GraphQLString),
#             'text': GraphQLInputObjectField(GraphQLString),
#             'tags': GraphQLInputObjectField(GraphQLList(GraphQLString)),
#         }


#     def get_output_fields(self):
#         return {
#             'post': GraphQLField(PostType),
#         }

#     def mutate(self, **params):
#         params['parent'] = params.pop('parent_id')
#         return asobj({'post': create_post(**params)})


# MutationType = GraphQLObjectType('Mutation', {
#     'addPost': AddPostMutation.build()

# })







def generate_schema(db):  
    _types = {}
    fields = {
        name: RootEntitySetField(entity, _types).as_graphql()
        for name, entity in db.entities.items()
    }

    query = GraphQLObjectType(name='Query', fields=fields)

    return GraphQLSchema(query=query)

