import typing
from contextlib import ExitStack

from django.db.models.sql import compiler
from django.db.models.sql.constants import MULTI, CURSOR, GET_ITERATOR_CHUNK_SIZE

from pgbackend._record_result import record_result
from pgbackend.connection import var_connection, get_connection


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

    def execute_sql(self, *, result_type, chunked_fetch, chunk_size, exitstack):
        assert chunked_fetch
        cursor_fn = self.connection.cursor
        self.connection.chunked_cursor = record_result(cursor_fn, record := {})
        try:
            result = super().execute_sql(
                result_type=result_type, chunked_fetch=chunked_fetch, chunk_size=chunk_size
            )
        finally:
            self.connection.chunked_cursor = cursor_fn
        assert isinstance(result, typing.Iterator)
        cursor = record['result']
        # extend connection lifetime
        exitstack = exitstack.pop_all()
        exitstack.callback(cursor.close)
        cursor._exit_cm = exitstack
        return result

    def execute_sql(
        self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE,
        execute_sql_keep_connection=execute_sql,
    ):
        is_new_connection = not get_connection()
        with ExitStack() as exit:
            exit.enter_context(self.connection.ensure_conn())
            if chunked_fetch and is_new_connection:
                result = execute_sql_keep_connection(
                    self, result_type=result_type, chunked_fetch=chunked_fetch, chunk_size=chunk_size,
                    exitstack=exit,
                )
            else:
                result = super().execute_sql(
                    result_type=result_type, chunked_fetch=chunked_fetch, chunk_size=chunk_size
                )
            if result_type == CURSOR:
                return Cursor.clone(result)
            return result


class SQLInsertCompiler(ExecuteSql, compiler.SQLInsertCompiler):
    pass


class SQLUpdateCompiler(compiler.SQLUpdateCompiler, SQLCompiler):
    pass


class SQLDeleteCompiler(SQLCompiler, compiler.SQLDeleteCompiler):
    pass
