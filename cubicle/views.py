import random

from greenbrew import green_spawn

from cubicle.models import Cubicle
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.


@green_spawn
def make(request):
    size = random.choice(range(1, 11))
    obj = Cubicle(size=size)
    obj.save()

    return JsonResponse({'size': obj.size})


@green_spawn
def show(request):
    params = Cubicle.objects.values('size')

    return JsonResponse(list(params), safe=False)
