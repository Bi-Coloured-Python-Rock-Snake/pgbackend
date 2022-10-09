from dataclasses import dataclass

import greenlet
import psycopg as psycopg
from django.db.models.sql.compiler import SQLCompiler

from greenbrew import green_spawn, green_async
from overriden import overriden as _overriden
from psycopg import AsyncConnection

from django.db.backends.postgresql.base import DatabaseWrapper

def replacement_condition_fn():
    return hasattr(greenlet.getcurrent(), 'spawning_greenlet')


overriden = lambda cls: _overriden(cls, replacement_condition_fn)

# class Connection(overriden(psycopg.Connection)):
#
#     connect = green_async(AsyncConnection.connect)

    # @classmethod
    # def connect(cls, *args, **kw):
    #     connect = green_async(AsyncConnection.connect)
    #     return connect(*args, **kw)


@dataclass
class Database:
    wrapped: object

    def __getattr__(self, item):
        return getattr(self.wrapped, item)


class DatabaseWrapper(overriden(DatabaseWrapper)):
    Database = Database(DatabaseWrapper.Database)
    Database.connect = green_async(AsyncConnection.connect)


#
# class SQLCompiler(overriden(SQLCompiler)):
#
#     @green_async
#     async def execute_sql(self, *args, execute_sql=SQLCompiler.execute_sql, **kw):
#         print('hi')
#         return execute_sql(self, *args, **kw)
#
