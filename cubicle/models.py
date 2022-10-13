from django.db import models

# Create your models here.


class Cubicle(models.Model):
    size = models.IntegerField()
    owner = models.ForeignKey('Souslik', related_name='guests', on_delete=models.CASCADE,
                              null=True)


class Souslik(models.Model):
    name = models.CharField(max_length=20)


class Food(models.Model):
    kg = models.DecimalField(max_digits=3, decimal_places=1)