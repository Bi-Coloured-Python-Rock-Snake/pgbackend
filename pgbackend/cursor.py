from psycopg import AsyncCursor, sql, AsyncConnection
from greenhack import  exempt


class AsyncConnection(AsyncConnection):

    #FIXME

    __enter__ = exempt(AsyncConnection.__aenter__)
    __exit__ = exempt(AsyncConnection.__aexit__)
    close = exempt(AsyncConnection.close)
    commit = exempt(AsyncConnection.commit)
    rollback = exempt(AsyncConnection.rollback)
    _set_autocommit = exempt(AsyncConnection.set_autocommit)
    _set_isolation_level = exempt(AsyncConnection.set_isolation_level)
    _set_read_only = exempt(AsyncConnection.set_read_only)


def connect(*args, **kw):
    ac = AsyncConnection(*args, **kw)
    ob = VirtualConnection()
    ob.ac = ac
    return ac


class VirtualConnection:
    pool: object

    @exempt
    async def close(self):
        await self.pool.close()

    @exempt
    async def commit(self):
        await self.ac.commit()


class AsyncCursor(AsyncCursor):

    # def cb(self, *ar, **kw):
    #     1

    execute = exempt(AsyncCursor.execute)
    executemany = exempt(AsyncCursor.executemany)
    fetchall = exempt(AsyncCursor.fetchall)
    fetchone = exempt(AsyncCursor.fetchone)
    fetchmany = exempt(AsyncCursor.fetchmany)
    close = exempt(AsyncCursor.close)
    copy = exempt(AsyncCursor.copy)

    __enter__ = exempt(AsyncCursor.__aenter__)
    __exit__ = exempt(AsyncCursor.__aexit__)

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
