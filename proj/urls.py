

from django.contrib import admin
from django.urls import path

from kitchen.views import kitchen, food_delivery, connect

urlpatterns = [
    path("admin/", admin.site.urls),
    path("kitchen/", kitchen),
    path("/", food_delivery),
    path("connect/", connect),
]
