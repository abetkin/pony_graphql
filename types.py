
from pony.orm import *


class EntityType:

    getters = {'id': 'get_by_id'}

    def __init__(self, entity):
        self.entity = entity

    def get_by_id(self, id):
        return self.entity.get(id=id)

    def get(self, **kwargs):
        getter = self.getters.values()[0]
        return getter(**kwargs)



class IntType:
    '''
    will be converted from int
    '''

    def make(self, entity):
        with db_session:
            1
