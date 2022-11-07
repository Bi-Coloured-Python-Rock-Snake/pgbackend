from django.db import connections
from django.db.transaction import Atomic

import pgbackend.base
from pgbackend import atomic


def __new__(cls, using, *args, **kwargs):
    db = connections[using]
    if isinstance(db, pgbackend.base.DatabaseWrapper):
        return atomic.Atomic(using, *args, **kwargs)
    return Atomic.__new__(Atomic, using, *args, **kwargs)


Atomic.__new__ = __new__
