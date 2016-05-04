import unittest

import sys, os

import pony
from pony import orm
from pony_graphql.ast_aware import QueryBuilder 

class QBuilderTest(unittest.TestCase):
    
    db_name = 'test_qbuilder.db'


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
    
        # import logging
        # logging.getLogger().setLevel(logging.INFO)
        # orm.sql_debug(True)
    
    @orm.db_session
    def test(self):
        qb = QueryBuilder(
            entity=self.db.Artist,
            paths=[
                ['genres', 'name']
            
            ],
            ifs=['x.age < 100'])
        items = qb.select()[:]
        print(items)