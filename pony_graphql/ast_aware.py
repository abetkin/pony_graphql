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

        

import os


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
    def entity_type(self):
        from pony_graphql._types import Query
        return Query.instance.field_types[self.entity.__name__]
    
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
        tree = PathTree.from_paths(self.paths, parent=self)
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
    
    # @cached_property
    # def list_roots(self): return {}
    
    def _make_path(self, path, index):
        # and populate self with it
        obj = self._get_path(path[:-1])
        
        list_root = None
        for i in range(1, len(path) + 1):
            p = path[:i]
            if self._is_list_type(p):
                list_root = p
                break
        
        if list_root:
            # li = List(list_root)
            # self.list_roots[list_root] = li
            ret = ListPath(path, list_root=list_root, index=index)
        else:
            ret = Path(path, index=index)
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
        # instantiate objects
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
    
    def instantiate(self, values, paths, filter_list_paths=True):
        root = self.__class__(parent=self.parent)
        list_paths = []
        list_values = []
        for path, value in zip(paths, values):
            if filter_list_paths and isinstance(path, ListPath):
                list_paths.append(path)
                list_values.append(value)
                continue
            d = root._get_path(path[:-1])
            d[path[-1]] = value
        if not filter_list_paths:
            return root
        list_values = zip(*list_values)
        
        list_roots = {}
        
        for p in list_paths:
            list_roots.setdefault(p.list_root, []).append(p.path)
        
        
        
        
        for list_root in list_roots:
            obj_list = []
            lpaths = list_roots[list_root]
            for vals in list_values:
                obj = self.instantiate(vals, list_paths, False)
                obj_list.append(obj)
            d = root._get_path(list_root[:-1])
            d[list_root[-1]] = obj_list
            

        return root
    

    def _is_list_type(self, path):
        typ = self.entity_type
        for key in path:
            typ.make_field_types()
            typ = typ.field_types[key]
        from pony_graphql._types import EntitySetType
        if isinstance(typ, EntitySetType):
            return True


class Path(object):
    preprocessing = False

    # def __new__(cls, *args, **kw):
    #     kw.pop('index')
    #     return tuple.__new__(cls, *args, **kw)
    
    def __init__(self, path, index):
        # self.index = kw.pop('index')
        self.index = index
        self.path = tuple(path)
        # tuple.__init__(self, *args, **kw)
    
    def __iter__(self):
        return iter(self.path)
    
    def __getitem__(self, index):
        return self.path[index]
    
    def on_value(self, pk, value):
        return value


class ListPath(Path):
    'with multiple values'
    
    preprocessing = True
    
    def __init__(self, path, index, list_root):
        Path.__init__(self, path, index)
        self.list_root = tuple(list_root)
    
    @cached_property
    def data(self): return {}
    
    def on_value_pre(self, pk, value):
        values = self.data.setdefault(pk, set())
        values.add(value)
    
    def on_value(self, pk, value):
        ret = self.data[pk]
        assert value in ret
        return list(ret)
