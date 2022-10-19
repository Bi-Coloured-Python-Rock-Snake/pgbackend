import random
from os.path import dirname
from pathlib import Path

from django.shortcuts import render
from greenhack import as_async

import myhttpx
from kitchen.models import Order, prepare_order
from proj import asgi

from django.http import JsonResponse, HttpResponse

from django.conf import settings

# Create your views here.

@as_async
def food_delivery(request):
    order: Order = prepare_order(request)
    order.save()
    resp = myhttpx.post(settings.KITCHEN_SERVICE, data=order.as_dict())
    match resp.status_code, resp.json():
        case 201, {"mins": _mins} as when:
            ws = asgi.consumers[request.user.username]
            ws.send_json(when)
            return JsonResponse(when)
        case _:
            kitchen_error(resp)


@as_async
def kitchen(request):
    if request.GET:
        request.POST = request.GET
    order_id = request.POST['order_id']
    mins = random.randrange(30, 60)
    return JsonResponse({'order_id': order_id, 'mins': mins}, status_code=201)


def connect(request):
    html = Path(dirname(__file__)) / 'ws.html'
    with open(html) as f:
        html = f.read()
    return HttpResponse(html)