
from django.db.backends.postgresql.base import DatabaseWrapper
from django.db.backends.postgresql.operations import DatabaseOperations


class DatabaseWrapper(DatabaseWrapper):
    ops_class = DatabaseOperations