from django.core.exceptions import EmptyResultSet
from django.db.models.sql.constants import MULTI, GET_ITERATOR_CHUNK_SIZE, NO_RESULTS, SINGLE, CURSOR
from greenhack import exempt



class C:

    async def execute_sql(self, *, result_type, cursor):
        result_type = result_type or NO_RESULTS
        try:
            sql, params = self.as_sql()
            if not sql:
                raise EmptyResultSet
        except EmptyResultSet:
            if result_type == MULTI:
                return iter([])
            else:
                return
        await cursor.execute(sql, params)

        if result_type == CURSOR:
            # Give the caller the cursor to process and close.
            return clone(cursor)
        if result_type == SINGLE:
            val = await cursor.fetchone()
            if val:
                return val[0: self.col_count]
            return val
        if result_type == NO_RESULTS:
            return

        result = await cursor.fetchall()
        return (result,)

    def execute_sql(
        self, result_type=MULTI, chunked_fetch=False, chunk_size=None,
        execute_sql=execute_sql,
    ):
        assert not chunked_fetch
        with self.connection.cursor() as cursor:
            return execute_sql(self, result_type=result_type, cursor=cursor)