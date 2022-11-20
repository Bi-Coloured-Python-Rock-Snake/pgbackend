from django.db import DEFAULT_DB_ALIAS
from django.db.backends.base.base import NO_DB_ALIAS
from django.db.backends.postgresql.base import DatabaseWrapper

from pgbackend.connection import PooledConnection, NoDbConnection
from pgbackend.ops import DatabaseOperations


class DatabaseWrapper(DatabaseWrapper):
    ops_class = DatabaseOperations

    _connection = None

    def __init__(self, settings_dict, alias=DEFAULT_DB_ALIAS):
        super().__init__(settings_dict, alias)
        self._connection = PooledConnection(db=self)

    @property
    def connection(self):
        return self._connection

    @connection.setter
    def connection(self, value):
        return
        # self._connection = value
    #FIXME

    def connect(self):
        # is not called
        # assert False
        #FIXME
        pass

    @property
    def ensure_conn(self):
        return self.connection.ensure_conn

    @property
    def transaction(self):
        return self.connection.transaction

    def _nodb_cursor(self):
        no_db = self.__class__({**self.settings_dict, "NAME": None}, alias=NO_DB_ALIAS)
        conn = NoDbConnection(no_db)
        return conn.cursor()

    def make_debug_cursor(self, cursor):
        return cursor

    def make_cursor(self, cursor):
        return cursor
