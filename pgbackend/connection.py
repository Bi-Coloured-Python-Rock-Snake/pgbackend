from contextlib import nullcontext, contextmanager, ExitStack
from functools import cached_property

import psycopg_pool
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.postgresql import base
from greenhack import exempt, exempt_cm, context_var
from psycopg import IsolationLevel
from psycopg.adapt import AdaptersMap
from psycopg.conninfo import make_conninfo

from pgbackend.cursor import CursorDebugWrapper, CursorWrapper

connection_context = context_var(__name__, 'connection_context', default=None)


def get_connection():
    exit = connection_context.get()
    if exit is None:
        return None
    assert isinstance(exit, ExitStack)
    return exit.conn


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

    @property
    def commit(self):
        assert (conn := get_connection())
        return exempt(conn.commit)

    @property
    def rollback(self):
        assert (conn := get_connection())
        return exempt(conn.rollback)

    #TODO add transaction method too?

    @exempt_cm
    def get_conn(self):
        if self.pool is None:
            self.start_pool()
        return self.pool.connection()

    @contextmanager
    def ensure_conn(self):
        with ExitStack() as exit:
            conn = exit.enter_context(self.get_conn())
            exit.conn = conn
            connection_context.set(exit)
            if not hasattr(conn, '_django_init'):
                conn._django_init = 'started'
                self.db.init_connection_state()
            exit.callback(lambda *exc_info: connection_context.set(None))
            yield conn

    def ensure_conn(self, ensure_conn=ensure_conn):
        if conn := get_connection():
            return nullcontext(conn)
        return ensure_conn(self)

    def cursor(self, *args, **kwargs):
        cm = connection_context.get()
        assert isinstance(cm, ExitStack)
        conn = cm.conn
        cursor = self.make_cursor(conn, *args, **kwargs)
        return cursor

    def cursor(self, *args, cursor=cursor, **kwargs):
        with self.ensure_conn():
            return cursor(self, *args, **kwargs)

    @exempt
    async def make_cursor(self, conn, *args, exit_cm=None, **kwargs):
        cursor = await conn.cursor(*args, **kwargs).__aenter__()
        if self.db.queries_logged:
            return CursorDebugWrapper(cursor, self.db, exit_cm=exit_cm)
        else:
            return CursorWrapper(cursor, self.db, exit_cm=exit_cm)

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
