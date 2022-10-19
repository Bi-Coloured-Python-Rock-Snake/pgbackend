from django.db import models

# Create your models here.


class Order(models.Model):
    pass


def prepare_order(request):
    return Order()