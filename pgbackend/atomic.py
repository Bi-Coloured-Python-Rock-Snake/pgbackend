from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import cached_property

from django.db import connections
from greenhack import exempt_cm

from pgbackend.connection import connection_var


@dataclass
class Atomic:
    using: str
    savepoint: bool
    durable: bool

    @property
    def __enter__(self):
        return self._cm.__enter__

    @property
    def __exit__(self):
        return self._cm.__exit__

    @cached_property
    def _cm(self):
        db = connections[self.using]
        return db.connection.get_conn()