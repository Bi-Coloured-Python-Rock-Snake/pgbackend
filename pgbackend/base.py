import typing
from dataclasses import dataclass

import psycopg_pool
from django.conf import settings
from django.db.backends.postgresql import base
from greenhack import exempt
from psycopg import IsolationLevel, AsyncCursor
from psycopg.adapt import AdaptersMap
from psycopg.conninfo import make_conninfo

from pgbackend.connection import PooledConnection
from pgbackend.cursor import CursorWrapper, CursorDebugWrapper


class DatabaseWrapper(base.DatabaseWrapper):
    from . import Database

    pool = None

    # a copy of the inherited method
    # will not be required
    # def get_new_connection(self, conn_params):
    #     Database = self.Database  # this is the missing line that was the reason to copy
    #     assert self.is_psycopg3
    #     ctx = base.get_adapters_template(settings.USE_TZ, self.timezone)
    #     connection = Database.connect(**conn_params, context=ctx)
    #
    #     # self.isolation_level must be set:
    #     # - after connecting to the database in order to obtain the database's
    #     #   default when no value is explicitly specified in options.
    #     # - before calling _set_autocommit() because if autocommit is on, that
    #     #   will set connection.isolation_level to ISOLATION_LEVEL_AUTOCOMMIT.
    #     options = self.settings_dict["OPTIONS"]
    #     try:
    #         isolevel = options["isolation_level"]
    #     except KeyError:
    #         self.isolation_level = IsolationLevel.READ_COMMITTED
    #     else:
    #         try:
    #             self.isolation_level = IsolationLevel(isolevel)
    #         except ValueError:
    #             raise base.ImproperlyConfigured(
    #                 "bad isolation_level: %s. Choose one of the "
    #                 "'psycopg.IsolationLevel' values" % (options["isolation_level"],)
    #             )
    #         connection.isolation_level = self.isolation_level
    #
    #     connection.cursor_factory = base.Cursor
    #
    #     return connection

    def get_new_connection(self, conn_params):
        return PooledConnection(conn_params=conn_params, db=self)


    # def cursor(self):
    #     if not in_ctx:
    #         ctx = ...
    #         enter_context(ctx)
    #     return EnterExit(self.cursor_enter, self.cursor_exit)
    #
    # @exempt
    # async def cursor_enter(self):
    #     conn = await self.pool.connection().__aenter__()
    #     cursor = await conn.cursor().__aenter__()
    #     cursorr.context.var.set(cursor)
    #     return cursor
    #
    # @exempt
    # async def cursor_exit(self, *exc_info):
    #     cursor = cursorr.context.var.get()
    #     await cursor.__aexit__(*exc_info)

    def make_debug_cursor(self, cursor):
        return cursor

    def make_cursor(self, cursor):
        return cursor
