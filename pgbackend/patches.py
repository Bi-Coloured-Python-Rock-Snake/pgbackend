from django.db.transaction import Atomic

from pgbackend import atomic


def __new__(cls, *args, **kwargs):
    return atomic.Atomic(*args, **kwargs)


Atomic.__new__ = __new__
