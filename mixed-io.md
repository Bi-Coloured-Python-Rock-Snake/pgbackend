Mixed I/O

This writing describes an alternative approach to writing async code: the 
mixed I/O. "Mixed" - because you mix "synchronous" and asynchronous 
code. With the traditional approach, that is not possible: you have to use 
async/await all 
the way down. However, you can use greenlets to remove this limitation.

One of the things that greenlet lets you do is to wrap an async function with a 
regular, non-async one. I will dwell on the implementation later. But what 
you can get from this is the compatibility between sync and async code.

With the traditional approach, sync and async code is not compatible: if you
need to support both sync and async I/O, you have to write two separate libraries.
Using greenlet can solve this. In fact, you 
can have the same code using async or blocking I/O, depending on a setting. 
This sounds like gevent. However, I want to propose a different variation on 
that, that doesn't involve monkey patching.

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

Here we have a django view that saves an order to the database, then makes a 
request to a service and notifies the customer by websocket about the result.
Despite not having async/await keywords, this is async code. myhttpx is a 
wrapper over the async httpx client. The async database backend is used that 
uses psycopg3. It 
is a 
working example, you can test it yourself.

The implementation is provided by [greenhack](https://github.
com/Bi-Coloured-Python-Rock-Snake/greenhack).

A few words on the implementation of greenlet: it is really a hack. It is 
not a part of any standard library or runtime (like POSIX). It manipulates the 
stack 
pointer using inline assembly, thus being specific to a CPU architecture.
However, this approach is quite often [used](https://en.wikipedia.org/wiki/Coroutine#C)
in C/C++ space.

Speaking about Python: besides greenlet, there is another implementation 
from PyPy. The latter is more minimalistic and probably suits the needs of 
`greenhack` better. However, greenlet is far more widely used and tested (by 
gevent, mainly).

Mixed I/O is a new approach to writing async code, but currently its best 
feature is that it can make django async! You take vanilla django, specify 
an async backend in the settings, and it just works.

rough comparison greenlet use