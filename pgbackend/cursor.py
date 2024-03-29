import functools
from typing import ContextManager

from creature import exempt, context_var, exempt_it
from django.db import NotSupportedError
from django.db.backends import utils
from psycopg import sql

cursor_var = context_var(__name__, 'cursor', default=None)


class CursorWrapper:
    _exit_cm: ContextManager = None

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

    @property
    def __iter__(self):
        return exempt_it(self.cursor.__aiter__)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    @property
    def __exit__(self, close=__exit__):
        if not self._exit_cm:
            return close.__get__(self)
        return self._exit_cm.__exit__

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
        # self.db.validate_no_broken_transaction()
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
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return await self.cursor.execute(sql)
            else:
                return await self.cursor.execute(sql, params)

    @exempt
    async def _executemany(self, sql, param_list, *ignored_wrapper_args):
        with self.db.wrap_database_errors:
            return await self.cursor.executemany(sql, param_list)

    @property
    def fetchmany(self):
        return exempt(self.cursor.fetchmany)

    @property
    def fetchall(self):
        return exempt(self.cursor.fetchall)

    @property
    def fetchone(self):
        return exempt(self.cursor.fetchone)

    @property
    def copy(self):
        return exempt(self.cursor.copy)

    def close(self):
        with self._exit_cm:
            pass

    @property
    def close(self, close_via_cm=close):
        if self._exit_cm:
            return close_via_cm.__get__(self)
        return exempt(self.cursor.close)


class CursorDebugWrapper(utils.CursorDebugWrapper, CursorWrapper, utils.CursorWrapper):
    pass
