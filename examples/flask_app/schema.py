import os, sys
# sys.path.insert(0, '../..')

import pony
from pony import orm
from pony_graphql import generate_schema

db_name = 'flask.db'



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


db.generate_mapping(check_tables=True, create_tables=True)

with orm.db_session:
    pop = Genre(name='pop')
    a = Artist(name='Sia', age=40, genres=[pop])

pony.options.INNER_JOIN_SYNTAX = True


schema = generate_schema(db)