import typing

from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.constants import MULTI, GET_ITERATOR_CHUNK_SIZE, CURSOR
from django.db.transaction import Atomic

from cm_decor import cm
from pgbackend import atomic


class Cursor(typing.NamedTuple):
    rowcount: int
    # lastrowid: str
    # description: tuple

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass

    @classmethod
    def clone(cls, cursor):
        return cls(rowcount=cursor.rowcount) #, lastrowid=cursor.lastrowid)


@cm
def execute_sql(
    self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE,
    execute_sql=SQLCompiler.execute_sql, *, cm
):
    cm.enter_context(self.connection.cursor())
    assert not chunked_fetch
    result = execute_sql(self, result_type=result_type)
    if result_type == CURSOR:
        return Cursor.clone(result)
    return result


SQLCompiler.execute_sql = execute_sql


def __init__(self, *args,
             __init__=Atomic.__init__,
             **kwargs):
    __init__(self, *args, **kwargs)
    self.__class__ = atomic.Atomic


Atomic.__init__ = __init__
