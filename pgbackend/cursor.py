from psycopg import AsyncCursor, sql, AsyncConnection
from shadow import hide


class AsyncConnection(AsyncConnection):

    __enter__ = hide(AsyncConnection.__aenter__)
    __exit__ = hide(AsyncConnection.__aexit__)
    close = hide(AsyncConnection.close)
    commit = hide(AsyncConnection.commit)
    rollback = hide(AsyncConnection.rollback)
    _set_autocommit = hide(AsyncConnection.set_autocommit)
    _set_isolation_level = hide(AsyncConnection.set_isolation_level)
    _set_read_only = hide(AsyncConnection.set_read_only)



class AsyncCursor(AsyncCursor):

    execute = hide(AsyncCursor.execute)
    executemany = hide(AsyncCursor.executemany)
    fetchall = hide(AsyncCursor.fetchall)
    fetchone = hide(AsyncCursor.fetchone)
    fetchmany = hide(AsyncCursor.fetchmany)
    close = hide(AsyncCursor.close)
    copy = hide(AsyncCursor.copy)

    __enter__ = hide(AsyncCursor.__aenter__)
    __exit__ = hide(AsyncCursor.__aexit__)

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
        self.execute(stmt)
        return args
