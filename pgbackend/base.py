import django
from django.db.backends.postgresql.base import *

from . import Database
import pgbackend.cursor

django.db.backends.postgresql.base.Database = Database

class DatabaseWrapper(DatabaseWrapper):
    Database = Database

    def get_new_connection(self, conn_params):
        connection = super().get_new_connection(conn_params)
        connection.cursor_factory = pgbackend.cursor.AsyncCursor
        return connection
