-SPLIT-
wrapping
greenlet impl
ways of use (gevent, sqlalchemy, djbackend)

Mixed I/O

This writing describes an alternative approach to writing async code: the 
mixed I/O. "Mixed" - because you can mix "synchronous" and asynchronous 
code. With the traditional approach that we all use, the code cannot be 
mixed: you have to use async/await all the way down. However, by using 
greenlets can work around that.

One of the things that greenlet lets you do is to wrap an async function into a 
regular, non-async one. I will dwell on the implementation later. But what 
you can get from this is the compatibility between sync and async code.

With the traditional approach, sync and async code is not compatible: you 
have to write two separate libraries for the same thing, if you need to 
support both sync and async I/O. Using greenlet can solve this. In fact, you 
can have the same code using async or blocking I/O depending on a setting. 
This sounds like gevent. However, I want to propose a different variation on 
that, that doesn't involve monkey patching.

Now, here is what it looks like, a gevent-like approach that I called "mixed 
I/O". A code example

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

Here you see a django view