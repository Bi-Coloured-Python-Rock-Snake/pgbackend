from contextlib import nullcontext, contextmanager
from functools import cached_property
from typing import AsyncContextManager

import psycopg_pool
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.postgresql import base
from greenhack import exempt, exempt_cm, context_var, exempt_it
from psycopg import IsolationLevel
from psycopg.adapt import AdaptersMap
from psycopg.conninfo import make_conninfo

from pgbackend._nullable_cm import nullable_cm
from pgbackend.cursor import CursorDebugWrapper, CursorWrapper, cursor_var

connection_var = context_var(__name__, 'connection', default=None)


class PooledConnection:
    pool = None

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

    @property
    def commit(self):
        assert (conn := connection_var.get())
        return exempt(conn.commit)

    @property
    def rollback(self):
        assert (conn := connection_var.get())
        return exempt(conn.rollback)

    #TODO add transaction method too?

    #TODO rename to get_conn
    def get_conn_async(self) -> AsyncContextManager:
        if self.pool is None:
            self.start_pool()
        return self.pool.connection()

    @contextmanager
    def ensure_conn(self, as_tuple=False):
        is_created = not (existing_conn := connection_var.get())
        if is_created:
            get_conn = exempt_cm(self.get_conn_async)
        else:
            get_conn = lambda: nullcontext(existing_conn)
        with get_conn() as conn:
            try:
                if not existing_conn:
                    connection_var.set(conn)
                if not hasattr(conn, '_django_init'):
                    conn._django_init = 'started'
                    self.db.init_connection_state()
                if as_tuple:
                    yield conn, is_created
                else:
                    yield conn
            finally:
                if is_created:
                    connection_var.set(None)

    def cursor(self, *args, **kwargs):
        with self.ensure_conn() as conn:
            create_cursor = exempt_cm(conn.cursor)
            cm = create_cursor(*args, **kwargs)
            cm = nullable_cm(cm)

            with cm as cursor:
                cm = cm.pop_context()
                cursor = self.make_cursor(cursor, cm=cm)
                return cursor

    def make_cursor(self, cursor, *, cm):
        if self.db.queries_logged:
            return CursorDebugWrapper(cursor, self.db, cm=cm)
        else:
            return CursorWrapper(cursor, self.db, cm=cm)

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
