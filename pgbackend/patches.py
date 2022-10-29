
from django.utils.connection import BaseConnectionHandler

import greenhack


class AllConnections:
    pass


#TODO store not connections, just current db?

class ConnectionsDesc:

    def __get__(self, instance, owner):
        if (ctx := greenhack.context.var.get()) is None:
            return instance.__dict__['_connections']
        try:
            return ctx.connections
        except AttributeError:
            ctx.connections = AllConnections()
            return ctx.connections

    def __set__(self, instance, value):
        instance.__dict__['_connections'] = value


BaseConnectionHandler._connections = ConnectionsDesc()