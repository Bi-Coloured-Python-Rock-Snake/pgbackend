from psycopg import *
from shadow import hide


class AsyncConnection(AsyncConnection):

    @hide
    async def _set_autocommit(self, value: bool) -> None:
        return await super().set_autocommit(value)


connect = hide(AsyncConnection.connect)
