from django.db.backends.postgresql.operations import DatabaseOperations


class DatabaseOperations(DatabaseOperations):
    compiler_module = "pgbackend.compiler"

    def compose_sql(self, sql, params):
        raise NotImplementedError
        return mogrify(sql, params, self.connection)