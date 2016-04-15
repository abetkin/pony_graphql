import pony
from pony import orm

import os, sys
import unittest

from graphql.core.language.parser import parse
from graphql.core.execution import execute

from pony_graphql.main import generate_schema


class Test(unittest.TestCase):

    db_name = 'test_int.db'


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
    
        import logging
        logging.getLogger().setLevel(logging.INFO)
        orm.sql_debug(True)
        
    def test_generation(self):
        schema = generate_schema(self.db)
        
        
            
        ast = parse('''
        query {
            Artist {
                age
                genres {
                    name
                }
            }
        }
        ''')
        with orm.db_session:
            result = execute(schema, None, ast)
            print(result.data)
            self.assertFalse(result.errors)
    
    def test_query(self):
        1
    
    def inter(self):
        import IPython
        IPython.embed()