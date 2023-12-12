from django.db import models
from django.utils import timezone
from django.db.models import JSONField
from django.contrib.auth.models import User


class Conversion(models.Model):
    date = models.DateField(default=timezone.now)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    user_parameters = JSONField(null=True)


class File(models.Model):
    date = models.DateField(default=timezone.now)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    conversion = models.ForeignKey(Conversion, on_delete=models.CASCADE)
    is_output = models.BooleanField(default=False)
    type = models.TextField()
    file = models.FileField(upload_to="", max_length=500)


class Transaction(models.Model):
    date = models.DateField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()


class Products(models.Model):
    name = models.TextField()
    get_display_number = models.IntegerField()
    get_display_price = models.FloatField()
    description = models.TextField()
    phrase = models.TextField()
