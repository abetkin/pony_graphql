import unittest

import sys, os

from cached_property import cached_property

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
    
    @cached_property
    def qbuilder(self):
        return QueryBuilder(
            entity=self.db.Artist,
            paths=[
                ['genres', 'name'],
                ['name'],
            ],
            ifs='x.age < 100')
    
    @cached_property
    def result(self):
        return {
            'name': 'Sia',
            'genres': {
                'name': 'pop',
            },
        }
    
    @orm.db_session
    def test(self):
    
        # TODO pony bug: ['name', 'name'] workaround
        items = self.qbuilder.make_select()
        self.assertEqual(len(items), 1)
        self.assertDictEqual(items[0], self.result)
    
    # TODO python3
    
    @orm.db_session
    def test_fors(self):
        1
    
    # TODO order_by
    
    @orm.db_session
    def test_order_by_args(self):
        self.qbuilder.order_by(self.db.Artist.name)
        r = self.qbuilder.make_select()
        print(r)
            
    @orm.db_session
    def test_order_by_func(self):
        g = self.db.Genre(name='rock')
        a = self.db.Artist(name='Umka', age=55, genres=[g])
        a = self.db.Artist(name='Fedorov', age=55, genres=[g])
        orm.flush()
        
        @self.qbuilder.order_by
        def _():
            return orm.desc(x.name)
        items = self.qbuilder.make_select()
        obj = items[0]
        self.assertEqual(obj.name, 'Umka')
        obj = items[-1]
        self.assertEqual(obj.name, 'Fedorov')