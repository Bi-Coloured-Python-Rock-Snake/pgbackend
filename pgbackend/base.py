from django.db import DEFAULT_DB_ALIAS
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.postgresql.base import DatabaseWrapper

from pgbackend.connection import PooledConnection
from pgbackend.ops import DatabaseOperations


class DatabaseWrapper(DatabaseWrapper):
    ops_class = DatabaseOperations

    def __init__(self, settings_dict, alias=DEFAULT_DB_ALIAS):
        super().__init__(settings_dict, alias)
        self.connection = PooledConnection(db=self)

    def connect(self):
        # is not called
        assert False

    @property
    def ensure_conn(self):
        return self.connection.ensure_conn

    @property
    def transaction(self):
        return self.connection.transaction

    # async def init_connection_state(self):
    #     BaseDatabaseWrapper.init_connection_state(self)
    #
    #     timezone_changed = self.ensure_timezone()
    #     if timezone_changed:
    #         # Commit after setting the time zone (see #17062)
    #         if not self.get_autocommit():
    #             self.connection.commit()

    def make_debug_cursor(self, cursor):
        return cursor

    def make_cursor(self, cursor):
        return cursor
