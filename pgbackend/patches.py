from django.db import connections
from django.db.transaction import Atomic

import pgbackend.base
from pgbackend import atomic


def __new__(cls, using, *args, __new__=Atomic.__new__,
            **kwargs):
    db = connections[using]
    match db:
        case pgbackend.base.DatabaseWrapper():
            return atomic.Atomic(using, *args, **kwargs)
        case _:
            return __new__(Atomic)


Atomic.__new__ = __new__
