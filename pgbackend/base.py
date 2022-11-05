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

    def get_new_connection(self, conn_params):
        return PooledConnection(db=self)

    def init_connection_state(self):
        "no-op"

    def make_debug_cursor(self, cursor):
        return cursor

    def make_cursor(self, cursor):
        return cursor
