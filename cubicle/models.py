from django.db import models

# Create your models here.


class Cubicle(models.Model):
    size = models.IntegerField()
