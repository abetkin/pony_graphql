
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
            ['id'],
            ['genres', 'name'],
            ['name'],
        ]
        
        import ipdb
        with ipdb.launch_ipdb_on_exception():
            items = [
                (1, 'rock', 'Sting'),
                (1, 'pop', 'Sting'),
                (2, 'jazz', 'Django'),
            ]
            tree = PathTree.from_paths(paths, parent=parent)
            objects = tree.iterate_through(items)
            self.assertEqual(
                list(objects),
                [
                    {
                        'genres': {'name': {'rock', 'pop'}},
                        'id': 1,
                        'name': 'Sting'
                    },
                    {
                        'genres': {'name': {'jazz'}},
                        'id': 2,
                        'name': 'Django'
                    }
                ]
            )
            

    def test2(self):
        from pony_graphql._types import Query
        # Artist = Query.instance.types_dict['Artist']
    
        class parent:
            _d = {}
            artist = EntityConnectionType(self.db.Artist, _d)
            genre = EntityConnectionType(self.db.Genre, _d)
            hobby = EntityConnectionType(self.db.Hobby, _d)
            artist.as_graphql()
            genre.as_graphql()
            hobby.as_graphql()
            
            entity_type = artist
            
            
        paths = [
            ['id'],
            ['genres', 'name'],
            ['hobbies', 'name'],
        ]
        
        import ipdb
        with ipdb.launch_ipdb_on_exception():
            items = [
                (1, 'rock', 'sport'),
                (1, 'pop', 'movies'),
                (2, 'jazz', 'music'),
                (2, 'jazz', 'movies'),
            ]
            tree = PathTree.from_paths(paths, parent=parent)
            objects = tree.iterate_through(items)
            self.assertEqual(
                list(objects), 
                    [
                    {
                        'genres': [
                            {'name': 'pop'},
                            {'name': 'rock'},
                        ],
                        'id': 1,
                        'hobbies': [
                            {'name': 'movies'},
                            {'name': 'sport'},
                        ],
                    },
                    {
                        'genres': [{'name': 'jazz'}],
                        'id': 2,
                        'hobbies': [
                            {'name': 'movies'},
                            {'name': 'music'},
                        ],
                    },
                ]
            )
        
    
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
        
        class Hobby(db.Entity):
            name = orm.Required(str)
            artists = orm.Set('Artist')
        
        class Artist(db.Entity):
            name = orm.Required(str)
            age = orm.Optional(int)
            hobbies = orm.Set(Hobby)
            genres = orm.Set(Genre)

        
        db.generate_mapping(check_tables=True, create_tables=True)
    
        with orm.db_session:
            pop = Genre(name='pop')
            a = Artist(name='Sia', age=40, genres=[pop])
    
        pony.options.INNER_JOIN_SYNTAX = True
    