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
        
        class Artist(db.Entity):
            name = orm.Required(str)
            age = orm.Optional(int)

        
        db.generate_mapping(check_tables=True, create_tables=True)
    
        with orm.db_session:            
            a = Artist(name='Sia', age=40)
    
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
            }
        }
        ''')

        result = execute(schema, None, ast)
    
    def test_query(self):
        1
    
    def inter(self):
        import IPython
        IPython.embed()