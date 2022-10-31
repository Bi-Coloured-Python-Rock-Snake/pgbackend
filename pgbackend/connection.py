from contextvars import ContextVar
from functools import cached_property

import psycopg_pool
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from greenhack import exempt
from psycopg import IsolationLevel
from psycopg.adapt import AdaptersMap
from psycopg.conninfo import make_conninfo

from pgbackend.cursor import CursorDebugWrapper, CursorWrapper

var = ContextVar('connection', default=None)

from django.db.backends.postgresql import base


#connect() starts a pool
class PooledConnection:
    pool: object = None

    def __init__(self, conn_params, db):
        self.conn_params = conn_params
        self.db = db

    def __getattr__(self, item):
        if conn := var.get():
            return getattr(conn, item)
        raise AttributeError

    async def make_pool(self):
        conninfo = make_conninfo(**self.conn_params)
        self.pool = psycopg_pool.AsyncConnectionPool(conninfo, open=False,
                                                configure=self.configure_connection)
        await self.pool.open()

    #TODO make cursor here?
    @exempt
    async def cursor(self):
        if self.pool is None:
            await self.make_pool()
        if not (conn := var.get()):
            conn = await self.pool.connection().__aenter__()
        cursor = conn.cursor()
        if self.db.queries_logged:
            return self.make_debug_cursor(cursor)
        else:
            return self.make_cursor(cursor)

    def make_debug_cursor(self, cursor):
        return CursorDebugWrapper(cursor, self.db)

    def make_cursor(self, cursor):
        return CursorWrapper(cursor, self.db)

    @cached_property
    def adapters(self):
        ctx = base.get_adapters_template(settings.USE_TZ, self.db.timezone)
        return AdaptersMap(ctx.adapters)

    async def configure_connection(self, connection):
        connection._adapters = self.adapters

        options = self.db.settings_dict["OPTIONS"]
        try:
            isolevel = options["isolation_level"]
        except KeyError:
            isolation_level = IsolationLevel.READ_COMMITTED
        else:
            try:
                isolation_level = IsolationLevel(isolevel)
            except ValueError:
                raise ImproperlyConfigured(
                    "bad isolation_level: %s. Choose one of the "
                    "'psycopg.IsolationLevel' values" % (options["isolation_level"],)
                )
        await connection.set_isolation_level(isolation_level)
