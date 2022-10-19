import random

from django.shortcuts import render
from greenhack import as_async

from kitchen.models import Order, prepare_order
from souslik import asgi

from django.http import JsonResponse

# Create your views here.

@as_async
def food_delivery(request):
    order: Order = prepare_order(request)
    order.save()
    resp = requests.post('https://kitchen-place.org/orders/', data=order.as_dict())
    match resp.status_code, resp.json():
        case 201, {"mins": mins} as when:
            ws = asgi.consumers[request.user.username]
            ws.send_json(when)
            return JsonResponse(when)
        case _:
            kitchen_error(resp)


@as_async
def kitchen(request):
    order_id = request.DATA['order_id']
    mins = random.randrange(30, 60)
    return JsonResponse({'order_id': order_id, 'mins': mins})