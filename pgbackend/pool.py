import pdb

import psycopg_pool
from greenhack import exempt
from psycopg.adapt import AdaptersMap
from psycopg.conninfo import make_conninfo



pool = None


@exempt
async def connect(*, context, **conn_params):
    global pool
    if not pool:
        async def configure(conn):
            conn._adapters = AdaptersMap(context.adapters)
        conninfo = make_conninfo(**conn_params)
        pool = psycopg_pool.AsyncConnectionPool(conninfo, open=False, configure=configure)
        await pool.open()

    conn = await pool.connection().__aenter__()
    return conn

