from django.db.backends.postgresql.operations import DatabaseOperations
from psycopg import AsyncClientCursor

from pgbackend.connection import get_connection


class DatabaseOperations(DatabaseOperations):
    compiler_module = "pgbackend.compiler"

    def compose_sql(self, sql, params):
        connection = get_connection()
        return AsyncClientCursor(connection).mogrify(sql, params)
