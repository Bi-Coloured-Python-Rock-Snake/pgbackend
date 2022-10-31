import typing

from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.constants import MULTI, GET_ITERATOR_CHUNK_SIZE, CURSOR


# class AllConnections:
#     pass
#
#
# #TODO store not connections, just current db?
#
# class ConnectionsDesc:
#
#     def __get__(self, instance, owner):
#         if (ctx := greenhack.context.var.get()) is None:
#             return instance.__dict__['_connections']
#         try:
#             return ctx.connections

#         except AttributeError:
#             ctx.connections = AllConnections()
#             return ctx.connections
#
#     def __set__(self, instance, value):
#         instance.__dict__['_connections'] = value
#
#
# BaseConnectionHandler._connections = ConnectionsDesc()

class Cursor(typing.NamedTuple):
    rowcount: int
    lastrowid: str
    # description: tuple

    @classmethod
    def clone(cls, cursor):
        return cls(rowcount=cursor.rowcount, lastrowid=cursor.lastrowid)


def execute_sql(
    self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE,
    execute_sql=SQLCompiler.execute_sql,
):
    assert not chunked_fetch
    result = execute_sql(self, result_type=result_type)
    if result_type != CURSOR:
        return result
    try:
        return Cursor.clone(result)
    finally:
        result.close()


SQLCompiler.execute_sql = execute_sql
