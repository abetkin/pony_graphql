
from pony import orm
from pony_graphql.ast_aware import PathTree
from pony_graphql._types import EntityConnectionType

import unittest


import sys, os

from cached_property import cached_property

import pony

class Test(unittest.TestCase):
    def test(self):
        from pony_graphql._types import Query
        # Artist = Query.instance.types_dict['Artist']
    
        class parent:
            _d = {}
            artist = EntityConnectionType(self.db.Artist, _d)
            genre = EntityConnectionType(self.db.Genre, _d)
            artist.as_graphql()
            genre.as_graphql()
            
            entity_type = artist
            
            
            paths = [
                ['genres', 'name'],
                ['name'],
            ]
        import ipdb
        with ipdb.launch_ipdb_on_exception():
            pt = PathTree(parent, parent.paths)
            # import ipdb; ipdb.set_trace()
            print(pt)
        
    
    db_name = 'test_pathtree.db'


    # @cached_property
    # def schema(self):
    #     return generate_schema(self.db)

    def setUp(self):
        db_path = os.path.dirname(__file__)
        db_path = os.path.join(db_path, self.db_name)
        try:
            os.remove(db_path)
        except OSError:
            pass
        db = self.db = orm.Database('sqlite', self.db_name, create_db=True)
        
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
    