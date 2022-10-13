from psycopg import AsyncCursor
from shadow import hide


class AsyncCursor(AsyncCursor):

    execute = hide(AsyncCursor.execute)
    executemany = hide(AsyncCursor.executemany)
    fetchall = hide(AsyncCursor.fetchall)
    fetchone = hide(AsyncCursor.fetchone)
    fetchmany = hide(AsyncCursor.fetchmany)
    close = hide(AsyncCursor.close)

    __enter__ = hide(AsyncCursor.__aenter__)
    __exit__ = hide(AsyncCursor.__aexit__)
