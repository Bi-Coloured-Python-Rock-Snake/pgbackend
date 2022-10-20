from django.db import models

# Create your models here.


class Order(models.Model):
    details = models.TextField()

    def as_dict(self):
        return {'order_id': self.id, 'details': self.details}


def prepare_order(request):
    details = request.POST.get('details', '')
    return Order(details=details)