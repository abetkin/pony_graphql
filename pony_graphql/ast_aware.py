import collections

from pony import orm, py23compat as compat
from graphql.core.execution.base import collect_fields
# from . import _types
from .util import ClassAttr, as_object, PassSelf

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
        tree = PathTree(parent=self)
        objects = tree.iterate_through(items)
        return list(objects)
    
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


class PathTree(dict):

    paths = None
    
    def _get_path(self, path):
        obj = self
        for key in path:
            if key not in obj:
                obj[key] = self.__class__(parent=self.parent)
            obj = obj[key]
        return obj
    
    def _make_path(self, path, index):
        # and populate self with it
        obj = self._get_path(path[:-1])
        
        is_list = any(
            self._is_list_type(path[:i])
            for i in range(1, len(path) + 1)
        )
        cls = ListPath if is_list else Path
        ret = cls(path, index=index)
        obj[path[-1]] = ret
        return ret
    
    @classmethod
    def from_paths(cls, paths, parent):
        root = cls(parent=parent)
        root.paths = []
        for i, p in enumerate(paths):
            path = root._make_path(p, i)
            root.paths.append(path)
        return root

    def __init__(self, parent):
        self.parent = parent
    
    def iterate_through(self, values):
        # preprocess
        for tupl in values:
            pk = tupl[0]
            for p, value in zip(self.paths, tupl):
                if p.preprocessing:
                    p.on_value_pre(pk, value)
        instantiated = set()
        for tupl in values:
            result = []
            pk = tupl[0]
            for p, value in zip(self.paths, tupl):
                result.append(
                    p.on_value(pk, value)
                )
            if pk not in instantiated:
                yield self.instantiate(result, self.paths)
                instantiated.add(pk)
        
    @property
    def entity_type(self):
        return self.parent.entity_type


    def __getattr__(self, key):
        return self.__getitem__(key)
    
    def instantiate(self, values, paths):
        root = self.__class__(parent=self.parent)
        for path, value in zip(paths, values):
            d = root._get_path(path[:-1])
            d[path[-1]] = value
        return root
    

    def _is_list_type(self, path):
        path = tuple(path)
        HACK = {
            ('genres', 'name'): True
        }
        # obj = self.entity_type
        # for key in path:
        #     obj.make_field_types()
        #     obj = obj.field_types[key]
        # return obj
        print(path, HACK.get(path))
        return HACK.get(path)


class Path(tuple):
    # not a listener for preproc.
    preprocessing = False

    index = None
    
    def __new__(cls, *args, **kw):
        kw.pop('index')
        return tuple.__new__(cls, *args, **kw)
    
    def __init__(self, *args, **kw):
        self.index = kw.pop('index')
        tuple.__init__(self, *args, **kw)
        
    

    def on_value(self, pk, value):
        print 'on_value', pk, value
        return value


class ListPath(Path):
    'with multiple values'
    
    preprocessing = True
    
    data = {}
    
    def on_value_pre(self, pk, value):
        li = self.data.setdefault(pk, [])
        li.append(value)
    
    def on_value(self, pk, value):
        ret = self.data[pk]
        assert value in ret
        return ret