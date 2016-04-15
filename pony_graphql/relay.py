'''
Node interface
clientMutationId
Connections
'''


class RelayMutationType:
    name = None

    def get_input_fields(self):
        raise NotImplementedError

    def get_output_fields(self):
        raise NotImplementedError

    def mutate(self, **params):
        raise NotImplementedError

    def _resolver(self, obj, args, info):
        params = args.get('input')
        result = self.mutate(**params)
        result.clientMutationId = params['clientMutationId']
        return result

    @classmethod
    def build(cls):
        self = cls()
        output_fields = self.get_output_fields()
        output_fields.update({
            'clientMutationId': GraphQLField(GraphQLNonNull(GraphQLString))
        })
        output_type = GraphQLObjectType(
            self.name + 'Payload',
            fields=output_fields)
        input_fields = self.get_input_fields()
        input_fields.update({
            'clientMutationId':
                GraphQLInputObjectField(GraphQLNonNull(GraphQLString))
        })
        input_arg = GraphQLArgument(GraphQLNonNull(GraphQLInputObjectType(
            name=self.name + 'Input',
            fields=input_fields)))
        return GraphQLField(
            output_type,
            args = {
                'input': input_arg,
            },
            resolver=self._resolver
        )



types = {}