import typing

from django.db.models.sql import compiler
from django.db.models.sql.constants import MULTI, CURSOR


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


class ExecuteSql:

    def execute_sql(self, *args, **kwargs):
        with self.connection.cursor():
            return super().execute_sql(*args, **kwargs)


class SQLCompiler(compiler.SQLCompiler):

    def execute_sql(self, result_type=MULTI, chunked_fetch=False, chunk_size=None):
        assert not chunked_fetch
        with self.connection.cursor():
            result = super().execute_sql(result_type=result_type)
            if result_type == CURSOR:
                return Cursor.clone(result)
            return result


class SQLInsertCompiler(ExecuteSql, compiler.SQLInsertCompiler):
    pass


class SQLDeleteCompiler(SQLCompiler, compiler.SQLDeleteCompiler):
    pass
