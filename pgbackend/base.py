from django.conf import settings
from django.db.backends.postgresql import base
from psycopg import IsolationLevel, AsyncCursor

from pgbackend.cursor import ConnWrapper, CursorWrapper, CursorDebugWrapper


class Wrapper:

    def __init__(self, base, **kw):
        self.base = base
        self.__dict__.update(kw)

    def __getattr__(self, item):
        return getattr(self.base, item)


class DatabaseWrapper(base.DatabaseWrapper):
    from . import Database

    pool = None

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        #TODO nodb
        # self.Database = Wrapper(self.Database, connect=self.get_conn_from_pool)

    # def cb(self, *args, **kw):
    #     1

    # @exempt()
    # async def get_conn_from_pool(self, *, context, **conn_params):
    #     if not self.pool:
    #         async def configure(conn):
    #             conn._adapters = AdaptersMap(context.adapters)
    #         conninfo = make_conninfo(**conn_params)
    #         self.pool = psycopg_pool.AsyncConnectionPool(conninfo, open=False, configure=configure)
    #         await self.pool.open()
    #     #TODO refactor
    #     connection = await self.pool.connection().__aenter__()
    #     return ConnWrapper(self.pool, connection)

    # a copy of the inherited method
    # will not be required
    def get_new_connection(self, conn_params):
        Database = self.Database  # this is the missing line that was the reason to copy
        assert self.is_psycopg3
        ctx = base.get_adapters_template(settings.USE_TZ, self.timezone)
        connection = Database.connect(**conn_params, context=ctx)

        # self.isolation_level must be set:
        # - after connecting to the database in order to obtain the database's
        #   default when no value is explicitly specified in options.
        # - before calling _set_autocommit() because if autocommit is on, that
        #   will set connection.isolation_level to ISOLATION_LEVEL_AUTOCOMMIT.
        options = self.settings_dict["OPTIONS"]
        try:
            isolevel = options["isolation_level"]
        except KeyError:
            self.isolation_level = IsolationLevel.READ_COMMITTED
        else:
            try:
                self.isolation_level = IsolationLevel(isolevel)
            except ValueError:
                raise base.ImproperlyConfigured(
                    "bad isolation_level: %s. Choose one of the "
                    "'psycopg.IsolationLevel' values" % (options["isolation_level"],)
                )
            connection.isolation_level = self.isolation_level

        connection.cursor_factory = base.Cursor

        return connection

    def get_new_connection(self, conn_params,
                           get_new_connection=get_new_connection):
        connection = get_new_connection(self, conn_params)
        connection.cursor_factory = AsyncCursor
        return ConnWrapper(connection, self)

    def make_debug_cursor(self, cursor):
        return CursorDebugWrapper(cursor, self)

    def make_cursor(self, cursor):
        return CursorWrapper(cursor, self)
