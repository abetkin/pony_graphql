# auto generation

from graphql.core.type.definition import GraphQLArgument, GraphQLField, GraphQLNonNull, \
    GraphQLObjectType, GraphQLList
from graphql.core.type.scalars import GraphQLString, GraphQLInt
from graphql.core.type.schema import GraphQLSchema
from graphql.core.type import GraphQLID, GraphQLInputObjectType, \
    GraphQLInputObjectField
    
from graphql.core.type.schema import GraphQLSchema

from _types import EntityType, EntitySetType
from mutations import BooleanResultMutation


def generate_schema(db):  
    _types = {}
    fields = {}
    mutations = {}
    for name, entity in db.entities.items():
        typ = EntitySetType(entity, _types)
        fields[name] = typ.make_field()
    
    for name, entity in db.entities.items():
        typ = EntityType(entity, _types)
        mutations.update(typ.make_mutations())


    InitAppMutation(db).register()

    if getattr(db, 'mutations', None):
        mutations.update(db.mutations)

    query = GraphQLObjectType(name='Query', fields=fields)
    mutation = GraphQLObjectType('Mutation', fields=mutations)



    return GraphQLSchema(query=query, mutation=mutation)

# from somewhere import mutation

# @mutation
# def init_app():
#     1


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


class InitAppMutation(DbMutation):
    name = 'initApp'

    def mutate(self):
        db = self.db
        rock = db.Genre(name='rock')
        a = db.Artist(name='Samoilov', age=45, genres=[rock])
        return True
        
