from functools import cached_property

from django.db import DEFAULT_DB_ALIAS
from django.db.backends.postgresql import base

from pgbackend.connection import PooledConnection
from pgbackend.ops import DatabaseOperations


class DatabaseWrapper(base.DatabaseWrapper):
    ops_class = DatabaseOperations

    def __init__(self, settings_dict, alias=DEFAULT_DB_ALIAS):
        super().__init__(settings_dict, alias)
        self.connection = PooledConnection(db=self)
        self.connection.start_pool()


    def get_new_connection(self, conn_params):
        raise NotImplementedError
        return PooledConnection(db=self)

    # @cached_property
    # def connection(self):
    #     return PooledConnection(db=self)

    def init_connection_state(self):
        "no-op"

    def make_debug_cursor(self, cursor):
        return cursor

    def make_cursor(self, cursor):
        return cursor
