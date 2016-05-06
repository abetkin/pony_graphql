import collections

from pony import orm, py23compat as compat
from graphql.core.execution.base import collect_fields
# from . import _types
from .util import ClassAttr, as_object

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

class Connection(object):
    
        def __init__(self, wrapped):
            self.wrapped = wrapped
        
        # def __setitem__(self, key, value):
        #     return getattr(self.wrapped, key)
        
        def __repr__(self):
            return 'Connection: %s' % self.wrapped
        
        @property
        def items(self):
            import ipdb; ipdb.set_trace()
            return list(self.wrapped)

        @property
        def __setitem__(self):
            return self.wrapped.__setitem__
        
        @property
        def edges(self):
            return [
                as_object({node: e})
                for e in self.wrapped
            ]
        


class Tree(dict):

    def __init__(self, *args, **kw):
        dict.__init__(self, *args, **kw)
        self.__dict__ = self

    def __contains__(self, key):
        return dict.__contains__(self, key)
        

    def new(self, key):
        new = self.__class__()
        new.entity_type = self.entity_type
        
        field = self.entity_type.field_types[key]
        from _types import EntitySetType
        if isinstance(field, EntitySetType):
            # import ipdb; ipdb.set_trace()
            new = new.Connection
        return new

    # Connection = cached_property(Connection)
    
    def Connection(self, *ar, **kw):
        1

    @classmethod
    def from_select(cls, paths, values):
        key = 'id'


    def update_from(self, paths, values):
        '''
        collect by key
        pass list forward
        '''
        # TODO
        # tree = combine(paths)
        # trees = [tree]
        # # tree -> values
        # parse(tree, values) -> [(tree, values)]
        
        
        # !! store paths, vals 
            

        for path, val in zip(self.paths, values):
            ret.set_at(path, val)
        return ret

    def set_at(self, path, value):
        obj = self
        for key in path[:-1]:
            if key not in obj:
                new = obj.new(key)
                obj[key] = new
            obj = obj[key]
                
        # import ipdb; ipdb.set_trace()
        self[path[-1]] = value
    
    # def 
    




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

    # TODO repr for tree
    def Tree(self, *args, **kw):
        inst = Tree(*args, **kw)
        inst.entity_type = self.entity_type
        return inst
        
        
    
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
        # FIXME group_by id
        ret = self.Tree()
        # Tree.set(paths, values)
        for path, val in zip(self.paths, values):
            ret.set_at(path, val)
        return ret