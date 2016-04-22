import os, sys
# sys.path.insert(0, '../..')

import pony
from pony import orm
from pony_graphql import generate_schema
from pony_graphql.mutations import EntityMutation, UpdateEntityMutation, DbMutation

db_name = 'flask.db'

from graphql.core.type import GraphQLInputObjectField, GraphQLInt

db_path = os.path.dirname(__file__)
db_path = os.path.join(db_path, db_name)
try:
    os.remove(db_path)
except OSError:
    pass
db = orm.Database('sqlite', db_name, create_db=True)

class Genre(db.Entity):
    name = orm.Required(str)
    artists = orm.Set('Artist')

class Artist(db.Entity):
    name = orm.Required(str)
    age = orm.Optional(int)
    genres = orm.Set(Genre)
    pieces = orm.Set('Piece')
    
    @EntityMutation.mark
    def customMutation(self):
        'Takes no args'
        
    @UpdateEntityMutation.mark
    def customUpdate(self, genres):
        '''
        Marked with UpdateEntityMutation, so
        can take keywords matching entity fields
        '''
        self.genres = [Genre[pk] for pk in genres]
        
    class changeAge(EntityMutation):
        '''
        You can also define custom mutation with a class
        '''
    
        def get_input_fields(self):
            ret = EntityMutation.get_input_fields(self)
            ret.update({
                'age': GraphQLInputObjectField(GraphQLInt)
            })
            return ret
            
        def mutate_func(self, obj, age):
            obj.age = age


class Piece(db.Entity):
    title = orm.Required(str)
    artist = orm.Required(Artist)


db.generate_mapping(check_tables=True, create_tables=True)

with orm.db_session:
    pop = Genre(name='pop')
    a = Artist(name='Sia', age=40, genres=[pop])
    Piece(title="Chandelier", artist=a)
    Piece(title="Bring it to me", artist=a)

pony.options.INNER_JOIN_SYNTAX = True

class InitAppMutation(DbMutation):
    name = 'initApp'

    def mutate(self):
        db = self.db
        rock = db.Genre(name='rock')
        a = db.Artist(name='Samoilov', age=45, genres=[rock])
        return True
        
InitAppMutation(db).register()

schema = generate_schema(db)
