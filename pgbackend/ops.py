from django.db.backends.postgresql.operations import DatabaseOperations


class DatabaseOperations(DatabaseOperations):
    compiler_module = "pgbackend.compiler"
