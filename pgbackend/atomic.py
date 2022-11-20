from dataclasses import dataclass
from functools import cached_property

from django.db.transaction import get_connection


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
        db = get_connection(self.using)
        return db.transaction()