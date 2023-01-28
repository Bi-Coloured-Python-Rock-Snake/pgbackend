import random
from os.path import dirname
from pathlib import Path

from creature import as_async
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

import myhttpx
from kitchen import ws
from kitchen.models import Order, prepare_order


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


@as_async
@csrf_exempt
def kitchen(request):
    if request.GET:
        request.POST = request.GET
    order_id = request.POST['order_id']
    mins = random.randrange(30, 60)
    return JsonResponse({'order_id': order_id, 'mins': mins}, status=201)


def connect(request):
    html = Path(dirname(__file__)) / 'ws.html'
    with open(html) as f:
        html = f.read()
    return HttpResponse(html)