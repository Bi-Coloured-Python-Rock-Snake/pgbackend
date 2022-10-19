from django.shortcuts import render

from kitchen.models import Order, prepare_order
from souslik import asgi


# Create your views here.

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


