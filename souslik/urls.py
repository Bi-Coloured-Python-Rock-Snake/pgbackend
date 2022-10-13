
from cubicle.views import show, make, index
from django.contrib import admin
from django.urls import path



urlpatterns = [
    path("admin/", admin.site.urls),
    path("show", show),
    path("make", make),
    path('', index),
]
