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
    type = models.TextField()
    file = models.FileField(upload_to='files/')

class Transaction(models.Model):
    date = models.DateField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
