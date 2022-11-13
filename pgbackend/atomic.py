from dataclasses import dataclass
from functools import cached_property

from django.db import connections


@dataclass
class Atomic:
    using: str
    savepoint: bool
    durable: bool

    def __enter__(self):
        return self._cm.__enter__()

    def __exit__(self, *exc_info):
        return self._cm.__exit__(*exc_info)

    @cached_property
    def _cm(self):
        db = connections[self.using]
        return db.connection.ensure_conn()