import collections

from pony import orm, py23compat as compat
from graphql.core.execution.base import collect_fields
# from . import _types

from cached_property import cached_property

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

    def __init__(self, *args, **kw):
        dict.__init__(self, *args, **kw)
        self.__dict__ = self

    def set_at(self, path, value):
        for key in path[:-1]:
            self = self.setdefault(key, self.__class__())
        self[path[-1]] = value




class QueryBuilder(object):
    
    order_by = None
    
    def __init__(self, entity, paths, ifs, fors=None, **kw):
        kw.update({
            'entity': entity,
            'paths': paths,
            'ifs': ifs,
            'fors': fors,
        })
        self.__dict__.update(kw)
    
    @cached_property
    def query(self):
        return orm.select(repr(self))
    
    
    
    @property
    def vars(self):
        # TODO
        return ['x']
    
    def __repr__(self):
        return ' '.join([
            self.get_paths(),
            self.get_fors(),
            self.get_ifs(),
        ])
    
    def order_by(self, f):
        self.query = self.query.order_by(f)
        return f
    
    def make_select(self):
        # import ipdb
        # with ipdb.launch_ipdb_on_exception():
            
        items = self.query[:]
        return [self._parse_result(values) for values in items]
    
    def get_paths(self):
        ret = []
        prefix = None
        if self.fors is None:
            prefix = 'x'
        for path in self.paths:
            if prefix:
                path = [prefix] + path
            ret.append(
                '.'.join(path)
            )
        return '[%s]' % ', '.join(ret)
    
    def get_ifs(self):
        if isinstance(self.ifs, compat.basestring):
            self.ifs = [self.ifs]
        return ' '.join(
            'if %s' % s.strip() for s in self.ifs
        )
    
    def get_fors(self):
        if self.fors:
            return self.fors
        return ' '.join([
            'for x in self.entity'
        ])
    
    def _parse_result(self, values):
        ret = Tree()
        for path, val in zip(self.paths, values):
            ret.set_at(path, val)
        return ret