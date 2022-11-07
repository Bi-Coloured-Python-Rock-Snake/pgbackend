from contextlib import contextmanager
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

    @exempt_cm
    def _cm(self):
        db = connections[self.using]
        pool = db.connection.pool
        return pool.connection()

    @cached_property
    @contextmanager
    def _cm(self, _cm=_cm):
        with _cm(self) as conn:
            connection_var.set(conn)
            try:
                yield
            finally:
                connection_var.set(None)
