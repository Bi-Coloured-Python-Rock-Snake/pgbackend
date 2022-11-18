from contextlib import nullcontext, asynccontextmanager
from functools import cached_property

import psycopg_pool
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.postgresql import base
from greenhack import exempt, context_var, as_async, universal_cm
from pgbackend.cursor import CursorDebugWrapper, CursorWrapper
from psycopg import IsolationLevel
from psycopg.adapt import AdaptersMap
from psycopg.conninfo import make_conninfo

var_connection = context_var(__name__, 'connection', default=None)


def get_connection():
    return var_connection.get()


class PooledConnection:
    pool = None

    def __init__(self, db):
        self.db = db

    def __getattr__(self, item):
        if conn := get_connection():
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

    def commit(self):
        assert (conn := get_connection())
        exempt(conn.commit)()

    def rollback(self):
        assert (conn := get_connection())
        exempt(conn.rollback)()

    @asynccontextmanager
    async def make_conn_async(self):
        if self.pool is None:
            await self.start_pool()
        async with self.pool.connection() as conn:
            var_connection.set(conn)
            if not hasattr(conn, '_django_init'):
                conn._django_init = 'started'
                init_connection_state = as_async(self.db.init_connection_state)
                await init_connection_state()
            try:
                yield conn
            finally:
                var_connection.set(None)

    @asynccontextmanager
    async def transaction(self):
        async with self.make_conn_async() as conn:
            async with conn.transaction():
                yield

    @universal_cm
    def transaction(self, transaction=transaction):
        if conn := get_connection():
            return conn.transaction()
        return transaction(self)

    @universal_cm
    def ensure_conn(self):
        if conn := get_connection():
            return nullcontext(conn)
        return self.make_conn_async()

    @exempt
    async def cursor(self, *args, **kwargs):
        async with self.ensure_conn() as conn:
            cursor = await conn.cursor(*args, **kwargs).__aenter__()
            cursor = self.make_cursor(cursor)
            return cursor

    def make_cursor(self, cursor):
        if self.db.queries_logged:
            return CursorDebugWrapper(cursor, self.db)
        else:
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
