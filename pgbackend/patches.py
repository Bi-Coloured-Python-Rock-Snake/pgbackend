from django.db.transaction import Atomic, get_connection

import pgbackend.atomic
import pgbackend.base


def __new__(cls, using, *args, __new__=Atomic.__new__,
            **kwargs):
    db = get_connection(using)
    match db:
        case pgbackend.base.DatabaseWrapper():
            return pgbackend.atomic.Atomic(using, *args, **kwargs)
        case _:
            return __new__(Atomic)


Atomic.__new__ = __new__
