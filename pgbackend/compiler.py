import typing

from django.db.models.sql import compiler
from django.db.models.sql.constants import MULTI, CURSOR, GET_ITERATOR_CHUNK_SIZE


class Cursor(typing.NamedTuple):
    rowcount: int
    # lastrowid: str
    # description: tuple

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass

    def close(self):
        pass

    @classmethod
    def clone(cls, cursor):
        return cls(rowcount=cursor.rowcount) #, lastrowid=cursor.lastrowid)


class ExecuteSql:

    def execute_sql(self, *args, **kwargs):
        with self.connection.ensure_conn():
            return super().execute_sql(*args, **kwargs)


class SQLCompiler(compiler.SQLCompiler):

    def execute_sql(
        self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE
    ):
        result = super().execute_sql(result_type=result_type, chunked_fetch=chunked_fetch, chunk_size=chunk_size)
        if result_type == CURSOR:
            return Cursor.clone(result)
        # elif chunked_fetch:
        #     assert isinstance(result, typing.Iterator)
        #
        #     def cur_iter(cm=cm.pop()):
        #         with cm:
        #             yield from result
        #
        #     return cur_iter()
        else:
            return result

    def execute_sql(
            self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE,
            execute_sql=execute_sql,
    ):
        with self.connection.ensure_conn():
            return execute_sql(
                self, result_type=result_type, chunked_fetch=chunked_fetch, chunk_size=chunk_size
            )



class SQLInsertCompiler(ExecuteSql, compiler.SQLInsertCompiler):
    pass


class SQLUpdateCompiler(compiler.SQLUpdateCompiler, SQLCompiler):
    pass


class SQLDeleteCompiler(SQLCompiler, compiler.SQLDeleteCompiler):
    pass
