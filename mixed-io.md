**Mixed I/O**

This describes an alternative approach to writing async code: mixed I/O.
"Mixed" - because you mix "synchronous" and asynchronous 
code. With the traditional approach, this is not possible: you have to use 
async/await all 
the way down.

It uses greenlets.
With greenlet, you can wrap an async function with a 
regular function. I will dwell on the implementation later. But what it 
gives you is, 
you achieve some compatibility between sync and async code.

Normally, sync and async code are not compatible: if you
need to support both sync and async I/O, you have to write two separate libraries.
greenlet can solve this. You 
can have the same code, being able to use async or blocking I/O, depending on a 
setting. 
This sounds like gevent. However, it doesn't involve monkey patching.

A code example

```python
from kitchen.models import Order

@as_async
def food_delivery(request):
    if request.GET:
        request.POST = request.GET
    order: Order = prepare_order(request)
    order.save()
    resp = myhttpx.post(settings.KITCHEN_SERVICE, data=order.as_dict())
    match resp.status_code, resp.json():
        case 201, {"mins": _mins} as when:
            if consumer := ws.consumers.get(request.user.username):
                consumer.send_json(when)
            return JsonResponse(when)
        case _:
            kitchen_error(resp)
```

Here we have a django view. It saves an order to the database, then makes a 
request to a service, then notifies the customer by websocket.
Despite not having async/await keywords, this is async code:

- it uses async database driver (psycopg3)
- myhttpx is a wrapper over the (async) httpx client
- websocket notification is of course asynchronous too

It is a working code, you can test it using these
[instructions](https://github.com/Bi-Coloured-Python-Rock-Snake/pgbackend).

The general implementation is provided by
[greenhack](https://github.com/Bi-Coloured-Python-Rock-Snake/greenhack).

A few words about it: greenlet is really a hack. It is 
not a part of any standard library or runtime (like POSIX). It manipulates the 
stack 
pointer using inline assembly, thus being not portable between CPU 
architectures.
However, the approach is quite [used](https://en.wikipedia.org/wiki/Coroutine#C)
in C/C++ space.

Speaking about Python: besides greenlet, there is another implementation 
from PyPy. The latter is more minimalistic and probably suits the needs of 
greenhack better. However, greenlet is far more widely used and tested - by 
gevent, mainly.

**Applied to django**

Mixed I/O is a new approach to writing async code in general. However, 
currently 
its best 
feature has been that it can make django async. You take vanilla django, 
specify an async backend in `settings.py`, and it just works. And you can use 
websocket connections too, finally!

This repository actually implements the async database backend for django
(for postgresql),
the 
rest of the code just serving testing purposes.

**Prior art: gevent and sqlalchemy**

I haven't seen the described approach being used anywhere. Here 
I will compare it to the other uses of greenlet I am aware of.

Gevent is the closest in terms of the approach. However, it uses greenlet to 
implement the concurrency, whereas "mixed i/o" - just as a bridge 
between the sync and async code. And it monkeypatches the 
standard library, which is no good.

Sqlalchemy is close in terms of the implementation. It also uses greenlet to 
bridge sync code to the async one, which lets it reuse the same codebase for 
its async API. However, it remains an implementation detail, no 
more. It is not visible outside: sqlalchemy provides an asynchronous API, in 
addition to the synchronous one, 
like any other async library would. This differs from the "mixed i/o" 
approach, when I can consume the same django API, only with the async I/O 
this time.


