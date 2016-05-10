import unittest

import sys, os

from cached_property import cached_property

import pony
from pony import orm
from pony_graphql.ast_aware import QueryBuilder
from pony_graphql import generate_schema

class Test(unittest.TestCase):
    
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
    
        generate_schema(self.db)
    
        # import logging
        # logging.getLogger().setLevel(logging.INFO)
        # orm.sql_debug(True)
    
    # @cached_property
    # def types(self):
    #     types = {}
    #     # import ipdb; ipdb.set_trace()
    #     generate_schema(self.db, types)
    #     return types
    
    @cached_property
    def qbuilder(self):
        ret = QueryBuilder(
            entity=self.db.Artist,
            paths=[
                ['genres', 'name'],
                ['name'],
            ],
            ifs='x.age < 100')
        # ret.entity_type = self.types['Artist']
        return ret
    
    # @cached_property
    # def result(self):
    #     return {
    #         'name': 'Sia',
    #         'genres': {
    #             'name': 'pop',
    #         },
    #     }
    
    @orm.db_session
    def test(self):
    
        # TODO pony bug: ['name', 'name'] workaround
        import ipdb
        with ipdb.launch_ipdb_on_exception():
            items = self.qbuilder.make_select()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0], {
                'name': 'Sia',
                'genres': [{
                    'name': 'pop',
                }],
            })
    
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
        self.db.Artist(name='Umka', age=55, genres=[g])
        self.db.Artist(name='Fedorov', age=53, genres=[g])
        orm.flush()
        
        @self.qbuilder.order_by
        def _():
            return orm.desc(x.name)
        items = self.qbuilder.make_select()
        obj = items[0]
        self.assertEqual(obj.name, 'Umka')
        obj = items[-1]
        self.assertEqual(obj.name, 'Fedorov')