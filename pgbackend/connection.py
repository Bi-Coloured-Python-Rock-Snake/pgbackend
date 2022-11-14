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

# connection_var = context_var(__name__, 'connection', default=None)
var_conn_cm = context_var(__name__, 'conn_cm', default=None)
#TODO connection_cm


def get_connection():
    return (cm := var_conn_cm.get()) and cm.conn


class PooledConnection:
    pool = None

    def __init__(self, db):
        self.db = db

    def __getattr__(self, item):
        # if conn := connection_var.get():
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
            conn = exit.conn = exit.enter_context(self.get_conn())
            var_conn_cm.set(exit)
            if not hasattr(conn, '_django_init'):
                conn._django_init = 'started'
                self.db.init_connection_state()
            exit.callback(lambda *exc_info: var_conn_cm.set(None))
            yield conn

    def ensure_conn(self, ensure_conn=ensure_conn):
        if conn := get_connection():
            return nullcontext(conn)
        return ensure_conn(self)

    def cursor(self, *args, conn_created, **kwargs):
        cm = var_conn_cm.get()
        assert isinstance(cm, ExitStack)
        conn = cm.conn
        if not conn_created:
            return self.make_cursor(conn, *args, **kwargs)
        cm = cm.pop_all()
        cursor = self.make_cursor(conn, *args, exit_cm=cm, **kwargs)
        cm.push(cursor.__exit__)
        return cursor

    def cursor(self, *args, cursor=cursor, **kwargs):
        existed = get_connection()
        with self.ensure_conn():
            return cursor(self, *args, conn_created=not existed, **kwargs)

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
