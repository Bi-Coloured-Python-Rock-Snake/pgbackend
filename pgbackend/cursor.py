from psycopg import AsyncCursor, sql
from shadow import hide


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
