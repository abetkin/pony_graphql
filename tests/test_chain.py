from collections import OrderedDict
import json
from graphql.core.execution import execute, Executor
from graphql.core.execution.middlewares.sync import SynchronousExecutionMiddleware
from graphql.core.language.parser import parse
from graphql.core.type import (GraphQLSchema, GraphQLObjectType, GraphQLField,
                               GraphQLArgument, GraphQLList, GraphQLInt, GraphQLString,
                               GraphQLBoolean)
from graphql.core.error import GraphQLError

from pony import orm
import pony

import os, sys

from pony_graphql import generate_schema

#
# genre -> artist -> piece -> title
#


    # tags = Json(['misc', 'prog'])
    
query = '''
Genre (id: 1) {
    artists (name: "Sia") {
        pieces (id: 1) {
            title
        }
    }
}
'''


import unittest

# class TestPony(unittest.TestCase):


    # @classmethod
    # def setUpClass(cls):        



# kwargs = {}
# if not os.path.exists(cls.db_name):
#     kwargs.update(create_db=True)
# db.bind('sqlite', cls.db_name, create_db=True)

    
        
    

# db.generate_mapping(check_tables=True, create_tables=True)

class TestChain(unittest.TestCase):

    db_name = 'a4.db'


    def setUp(self):
        db_path = os.path.dirname(__file__)
        db_path = os.path.join(db_path, self.db_name)
        try:
            os.remove(db_path)
        except OSError:
            pass
        db = self.db = orm.Database('sqlite', self.db_name, create_db=True)
        
        class Artist(db.Entity):
            name = orm.Required(str)
            genres = orm.Set('Genre')
            pieces = orm.Set('Piece')
        
        class Piece(db.Entity):
            title = orm.Required(str)
            artist = orm.Required(Artist)

        class Genre(db.Entity):
            title = orm.PrimaryKey(str)
            artists = orm.Set(Artist)
        
        
        db.generate_mapping(check_tables=True, create_tables=True)
    
        with orm.db_session:            
            g = Genre(title='pop')
            a = Artist(name='Sia', genres=[g])
            song = Piece(title='Chandelier', artist=a)
    
        pony.options.INNER_JOIN_SYNTAX = True
    
        import logging
        logging.getLogger().setLevel(logging.INFO)
        orm.sql_debug(True)
#     # @classmethod
#     # # @orm.db_session
#     # def tearDownClass(cls):
#     #     cls.db.drop_all_tables()
    
    # __call__ = orm.db_session(unittest.TestCase.__call__)
    
    @orm.db_session
    def test(self):
        song = orm.select(p for p in Piece).first()
        def g():
            for ge in Genre:
                for a in ge.artists:
                    if a.name == 'Sia':
                        for p in a.pieces:
                            yield p
        pi = orm.select(g())[:]
        self.assertEqual(song.title, 'Chandelier')
    
    @orm.db_session    
    def test_2(self):
        db = self.db
        qs = orm.select(p for p in db.Piece for a in db.Artist for ge in db.Genre
            if p.artist == a
            if ge.title == 'pop'
            if orm.JOIN(a in ge.artists)
        )[:]
        IPython.embed()

    @orm.db_session    
    def test_3(self):
        db = self.db
        
        def g():
            for a in db.Artist:
                for p in a.pieces:
                    yield p
        
        # qs = orm.select(*(p for p in a.pieces) for a in db.Artist 
            # if p.artist == a
            # if ge.title == 'pop'
            # if orm.JOIN(a in ge.artists)
        # qs = orm.select(g())[:]
        qs = orm.select(p for a in db.Artist for ge in db.Genre
            for p in ge.artists.pieces
            if a.name == 'Sia'
            if orm.JOIN(a in ge.artists)
            )[:]
        IPython.embed()


