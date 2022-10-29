from dataclasses import dataclass

import greenhack
from greenhack import exempt
from psycopg import AsyncCursor, sql

from django.db.backends import utils

from . import pool


def get_db():
    ctx = greenhack.context.var.get()
    return ctx.connections.default



class ConnWrapper:
    def __init__(self, conn, db):
        self.conn = conn
        self.db = db

    # conn in django is meant to be reused
    # so conn.close() is called when all db connections need to be closed
    #

    def __getattr__(self, attr):
        return getattr(self.conn, attr)

    def __setattr__(self, name, value):
        if name == 'conn' or name == 'db':
            super().__setattr__(name, value)
        elif name == 'autocommit':
            self._set_autocommit(value)
        else:
            setattr(self.conn, name, value)

    @exempt
    async def close(self):
        await self.conn.close()

    @exempt
    async def commit(self):
        await self.conn.commit()

    @exempt
    async def rollback(self):
        await self.conn.rollback()

    @exempt
    async def __enter__(self):
        return await self.conn.__aenter__()

    @exempt
    async def __exit__(self, exc_type, exc_val, exc_tb):
        return await self.conn.__aexit__(exc_type, exc_val, exc_tb)

    @exempt
    async def _set_autocommit(self, value):
        return await self.conn.set_autocommit(value)

    @exempt
    async def _set_isolation_level(self, value):
        return await self.conn.set_isolation_level(value)

    @exempt
    async def _set_read_only(self, value):
        return await self.conn.set_read_only(value)

    def cursor(self):
        cursor = self.conn.cursor()
        return CursorWrapper(cursor, self.db)


#TODO set connection = None in base.py


#TODO context conn, sometimes None

# class AsyncCursor(AsyncCursor):
#
#     execute = exempt(AsyncCursor.execute)
#     executemany = exempt(AsyncCursor.executemany)
#     fetchall = exempt(AsyncCursor.fetchall)
#     fetchone = exempt(AsyncCursor.fetchone)
#     fetchmany = exempt(AsyncCursor.fetchmany)
#     copy = exempt(AsyncCursor.copy)
#
#     __enter__ = exempt(AsyncCursor.__aenter__)
#     __exit__ = exempt(AsyncCursor.__aexit__)
#
#     def callproc(self, name, args=None):
#         if not isinstance(name, sql.Identifier):
#             name = sql.Identifier(name)
#
#         qparts = [sql.SQL("select * from "), name, sql.SQL("(")]
#         if args:
#             for item in args:
#                 qparts.append(sql.Literal(item))
#                 qparts.append(sql.SQL(","))
#             del qparts[-1]
#
#         qparts.append(sql.SQL(")"))
#         stmt = sql.Composed(qparts)
#         self.execute(stmt)
#         return args
#
#     @exempt
#     async def close(self, _close=AsyncCursor.close):
#         await _close(self)
#


class CursorWrapper:
    def __init__(self, cursor, db):
        self.cursor = cursor
        self.db = db

    WRAP_ERROR_ATTRS = frozenset(["fetchone", "fetchmany", "fetchall", "nextset"])

    def __getattr__(self, attr):
        cursor_attr = getattr(self.cursor, attr)
        if attr in CursorWrapper.WRAP_ERROR_ATTRS:
            return self.db.wrap_database_errors(cursor_attr)
        else:
            return cursor_attr

    def __iter__(self):
        #TODO
        raise NotImplementedError
        with self.db.wrap_database_errors:
            yield from self.cursor

    def __enter__(self):
        return self

    @exempt
    async def __exit__(self, type, value, traceback):
        # Close instead of passing through to avoid backend-specific behavior
        # (#17671). Catch errors liberally because errors in cleanup code
        # aren't useful.
        try:
            await self.cursor.close()
        except self.db.Database.Error:
            pass

    # The following methods cannot be implemented in __getattr__, because the
    # code must run when the method is invoked, not just when it is accessed.

    def callproc(self, name, args=None):
        if not isinstance(name, sql.Identifier):
            name = sql.Identifier(name)

        qparts = [sql.SQL("select * from "), name, sql.SQL("(")]
        if args:
            for item in args:
                qparts.append(sql.Literal(item))
                qparts.append(sql.SQL(","))
            del qparts[-1]

        qparts.append(sql.SQL(")"))
        stmt = sql.Composed(qparts)
        self.cursor.execute(stmt)
        return args

    def callproc(self, procname, params=None, kparams=None,
                 callproc=callproc):
        # Keyword parameters for callproc aren't supported in PEP 249, but the
        # database driver may support them (e.g. cx_Oracle).
        if kparams is not None and not self.db.features.supports_callproc_kwargs:
            raise NotSupportedError(
                "Keyword parameters for callproc are not supported on this "
                "database backend."
            )
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None and kparams is None:
                return callproc(self, procname)
            elif kparams is None:
                return callproc(self, procname, params)
            else:
                params = params or ()
                return callproc(self, procname, params, kparams)

    def execute(self, sql, params=None):
        return self._execute_with_wrappers(
            sql, params, many=False, executor=self._execute
        )

    def executemany(self, sql, param_list):
        return self._execute_with_wrappers(
            sql, param_list, many=True, executor=self._executemany
        )

    def _execute_with_wrappers(self, sql, params, many, executor):
        context = {"connection": self.db, "cursor": self}
        for wrapper in reversed(self.db.execute_wrappers):
            executor = functools.partial(wrapper, executor)
        return executor(sql, params, many, context)

    @exempt
    async def _execute(self, sql, params, *ignored_wrapper_args):
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return await self.cursor.execute(sql)
            else:
                return await self.cursor.execute(sql, params)

    @exempt
    async def _executemany(self, sql, param_list, *ignored_wrapper_args):
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            return await self.cursor.executemany(sql, param_list)

    #TODO ineffective?
    @exempt
    async def fetchmany(self, size=0):
        return await self.cursor.fetchmany(size)

    @exempt
    async def fetchall(self):
        return await self.cursor.fetchall()

    @exempt
    async def fetchone(self):
        return await self.cursor.fetchone()

    @exempt
    async def copy(self):
        return await self.cursor.copy()

    @exempt
    async def close(self):
        return await self.cursor.close()


class CursorDebugWrapper(utils.CursorDebugWrapper, CursorWrapper, utils.CursorWrapper):
    pass
