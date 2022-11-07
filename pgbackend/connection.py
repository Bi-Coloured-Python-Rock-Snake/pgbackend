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
    def get_conn(self):
        return self.pool.connection()

    @contextmanager
    def get_conn(self, get_conn=get_conn):
        if existing_conn := connection_var.get():
            cm = nullcontext(existing_conn)
        else:
            cm = get_conn(self)
        with cm as conn:
            try:
                if not existing_conn:
                    connection_var.set(conn)
                if not getattr(conn, '_django_initialized', False):
                    conn._django_initialized = True
                    self.db.init_connection_state()
                yield conn
            finally:
                if not existing_conn:
                    connection_var.set(None)

    @exempt_cm
    def cursor(self, conn):
        return conn.cursor()

    @contextmanager
    def cursor(self, cursor_cm=cursor):
        with self.get_conn() as conn:
            with cursor_cm(self, conn) as cur:
                cur = self.make_cursor(cur)
                try:
                    cursor_var.set(cur)
                    yield cur
                finally:
                    cursor_var.set(None)

    # FIXME make ._cm attribute in cursor
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
