import collections

from pony import orm
from graphql.core.execution.base import collect_fields
# from . import _types



class AstTraverser(object):

    def __init__(self, info):
        self.__dict__.update(info.__dict__)
    
    
    def __iter__(self, field_asts=None, chain=None):
        if chain is None:
            chain = []
        if field_asts is None:
            field_asts = self.field_asts
        for field_ast in field_asts:
            selection_set = field_ast.selection_set
            if selection_set:
                subfield_asts = collect_fields(
                    self.context, self.return_type, selection_set,
                    collections.defaultdict(list),
                    set()
                )
                for field_name, asts in subfield_asts.items():
                    new_chain = chain + [field_name]
                    for result in self.__iter__(field_asts=asts, chain=new_chain):
                        yield result
            else:
                yield chain

        


# class ConnectionType(_types.EntityConnectionType):
    
#     def __call__(self, obj, kwargs, info):
#         traverser = AstTraverser(info)


import os


class Tree(dict):

    def __init__(self, args, **kw):
        dict.__init__(self, args, **kw)
        self.__dict__ = self

    def set_at(self, path, value):
        for key in path[:-1]:
            self = self.setdefault(key, self.__class__())
        self[path[-1]] = value


class QueryBuilder(object):
    
    def __init__(self, entity, paths, ifs, fors=None, **kw):
        kw.update({
            'entity': entity,
            'paths': paths,
            'ifs': ifs,
            'fors': fors,
        })
        self.__dict__.update(kw)
    
    def __repr__(self):
        return ' '.join([
            self.get_selects(),
            self.get_fors(),
            self.get_ifs(),
        ])
        
    def select(self):
        return orm.select(repr(self))
    
    def get_selects(self):
        ret = []
        prefix = None
        if not getattr(self, 'fors', None):
            prefix = 'x'
        for path in self.paths:
            if prefix:
                path = [prefix] + path
            ret.append(
                '.'.join(path)
            )
        ret = '[%s]' % ', '.join(ret)
        return ret
    
    def get_ifs(self):
        return ' '.join(
            'if %s' % s.strip() for s in self.ifs
        )
    
    def get_fors(self):
        if getattr(self, 'fors', None):
            return self.fors
        return ' '.join([
            'for x in self.entity'
        ])
    
    def parse_result(self, items):
        ret = Tree()
        for path, val in zip(self.paths, items):
            ret.set_at(path, val)
        return ret