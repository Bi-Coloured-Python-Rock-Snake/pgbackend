from contextlib import nullcontext, contextmanager
from functools import cached_property

import psycopg_pool
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.postgresql import base
from greenhack import exempt, exempt_cm, context_var
from psycopg import IsolationLevel
from psycopg.adapt import AdaptersMap
from psycopg.conninfo import make_conninfo

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

    @exempt_cm
    def get_conn(self):
        return self.pool.connection()

    @contextmanager
    def get_conn(self, get_conn=get_conn):
        if existing_conn := connection_var.get():
            cm = nullcontext(existing_conn)
        else:
            if self.pool is None:
                self.start_pool()
            cm = get_conn(self)
        with cm as conn:
            try:
                if not existing_conn:
                    connection_var.set(conn)
                if not hasattr(conn, '_django_init'):
                    conn._django_init = 'started'
                    self.db.init_connection_state()
                yield conn
            finally:
                if not existing_conn:
                    connection_var.set(None)

    @contextmanager
    def cursor(self):
        with self.get_conn() as conn:
            cursor_cm = exempt_cm(conn.cursor)
            with cursor_cm() as cur:
                cur = self.make_cursor(cur)
                try:
                    cursor_var.set(cur)
                    yield cur
                finally:
                    cursor_var.set(None)

    def cursor(self, cursor_cm=cursor):
        if cur := cursor_var.get():
            return cur
        return cursor_cm(self)

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
