import asyncio
from functools import wraps

from greenhack import exempt, as_async


def wrap_co(co_func):
    @wraps(co_func)
    def wrapper(*args, **kwargs):
        gen = co_func(*args, **kwargs)
        val = None
        while 1:
            try:
                val = gen.send(val)
            except StopIteration as ex:
                return ex.value
            if val == 'start':
                def fun():
                    val = gen.send('started')
                    assert val == 'end'
                task = as_async(fun)()
                task = asyncio.create_task(task)
                yield from task
            else:
                yield val

    return wrapper


class Start:
    def __await__(self):
        yielded = yield 'start'
        assert yielded == 'started'


class End:
    def __await__(self):
        yielded = yield 'end'
        assert yielded == 'start'



class IO:
    def __aenter__(self):
        return Start()

    def __aexit__(self, exc_type, exc_val, exc_tb):
        return End()

io = IO()

@exempt
async def sleep(sec):
    await asyncio.sleep(sec)
    return sec


@exempt
@as_async
def recurse():
    x = sleep(0.3)
    print(x)


async def main():
    async with io:
        x = sleep(0.5)
        print(x)

    await asyncio.sleep(0.5)
    print(0.5)

    async with io:
        recurse()
