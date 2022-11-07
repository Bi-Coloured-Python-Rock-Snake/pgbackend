from contextlib import asynccontextmanager, nullcontext, contextmanager
from contextvars import ContextVar
from functools import cached_property

import psycopg_pool
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.postgresql import base
from greenhack import exempt, exempt_cm
from psycopg import IsolationLevel
from psycopg.adapt import AdaptersMap
from psycopg.conninfo import make_conninfo

from pgbackend.cursor import CursorDebugWrapper, CursorWrapper, cursor_var


connection_var = ContextVar('connection', default=None)


class PooledConnection:

    def __init__(self, db):
        self.db = db

    def __getattr__(self, item):
        if conn := connection_var.get():
            return getattr(conn, item)
        raise AttributeError

    @exempt
    async def start_pool(self):
        conn_params = self.db.get_connection_params()
        conninfo = make_conninfo(**conn_params)
        pool = psycopg_pool.AsyncConnectionPool(conninfo, open=False,
                                                configure=self.configure_connection)
        await pool.open()
        self.pool = pool

    @exempt_cm
    @asynccontextmanager
    async def cursor(self):
        if not (_conn := connection_var.get()):
            conn_ct = self.pool.connection()
        else:
            conn_ct = nullcontext()
        async with conn_ct as conn:
            conn = conn or _conn
            async with conn.cursor() as cur:
                yield self.make_cursor(cur)

    @contextmanager
    def cursor(self, cursor_cm=cursor):
        with cursor_cm(self) as cur:
            try:
                cursor_var.set(cur)
                yield
            finally:
                cursor_var.set(None)

    def cursor(self, cursor_cm=cursor):
        if cur := cursor_var.get():
            return cur
        return cursor_cm(self)

    def make_cursor(self, cursor):
        return CursorDebugWrapper(cursor, self.db)

    def make_cursor(self, cursor, make_debug_cursor=make_cursor):
        if self.db.queries_logged:
            return make_debug_cursor(self, cursor)
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

        #TODO init_connection_state