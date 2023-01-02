from django.db.backends.postgresql.operations import DatabaseOperations
from psycopg import AsyncClientCursor, errors


class DatabaseOperations(DatabaseOperations):
    compiler_module = "pgbackend.compiler"

    def compose_sql(self, sql, params):
        raise NotImplementedError

    def last_executed_query(self, cursor, sql, params):
        try:
            AsyncClientCursor(cursor.connection).mogrify(sql, params)
        except errors.DataError:
            return None
