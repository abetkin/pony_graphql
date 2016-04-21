
import json
from collections import OrderedDict, namedtuple

class ClassAttr(object):
    def __init__(self, attr_name):
        self.attr_name = attr_name
    
    def __get__(self, isinstance, owner):
        return getattr(owner, self.attr_name)


class CallableCollector(dict):
    registry = OrderedDict()

    def __call__(self, func=None, **kw):
        info = self.__class__(self, **kw)
        if func:
            name = info.setdefault('name', func.__name__)
            info['callable'] = func
            self.registry[name] = info
            return func
        return info


class as_object(object):
    
    def __init__(self, d):
        self.__dict__ = d
        
    def __repr__(self):
        return repr(self.__dict__)



