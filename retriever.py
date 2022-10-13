import httpx as httpx
from shadow import hide


def make_method(method):
    @hide
    async def wrapper(*args, **kw):
        async with httpx.AsyncClient() as client:
            return await getattr(client, method)(*args, **kw)

    wrapper.__name__ = method
    return wrapper


get = make_method('get')
post = make_method('post')