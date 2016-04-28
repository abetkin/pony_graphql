import collections

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
    
        