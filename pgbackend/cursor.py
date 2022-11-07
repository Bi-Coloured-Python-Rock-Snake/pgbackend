import functools
from contextvars import ContextVar

from django.db import NotSupportedError
from django.db.backends import utils
from greenhack import exempt
from psycopg import sql


cursor_var = ContextVar('cursor', default=None)


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

    def __exit__(self, type, value, traceback):
        pass
        # Close instead of passing through to avoid backend-specific behavior
        # (#17671). Catch errors liberally because errors in cleanup code
        # aren't useful.
        # try:
        #     self.close()
        # except self.db.Database.Error:
        #     pass

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

    # @exempt
    # async def close(connection):
    #     # await connection.commit()
    #     await connection.__aexit__(None, None, None)

    def close(self):
        pass
        # exempt(self.cursor.close)()
        # if not (conn := connection.connection_var.get()):
        #     return
        # (conn, cursor_scope) = conn
        # if cursor_scope:
        #     assert conn is self.cursor.connection
        #     commit_and_close(conn)
        #     connection.connection_var.set(None)


class CursorDebugWrapper(utils.CursorDebugWrapper, CursorWrapper, utils.CursorWrapper):
    pass
