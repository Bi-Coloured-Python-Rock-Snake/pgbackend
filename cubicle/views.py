import random
from os.path import dirname
from pathlib import Path

from shadow import reveal

from cubicle.models import Cubicle
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.


@reveal
def make(request):
    size = random.choice(range(1, 11))
    obj = Cubicle(size=size)
    obj.save()

    return JsonResponse({'size': obj.size})


@reveal
def show(request):
    params = Cubicle.objects.values('size')

    return JsonResponse(list(params), safe=False)


@reveal
def send(request):
    from souslik import asgi
    consumer = asgi.consumers[request.user.username]
    consumer.send_json(['yo'])
    return HttpResponse('ok')


def index(request):
    html = Path(dirname(__file__)) / 'testws.html'
    with open(html) as f:
        html = f.read()
    return HttpResponse(html)