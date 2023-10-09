from django.db import models

from django.db import models
from django.db.models import JSONField

ROLE_TYPES = [
    ('ADMIN', 'Admin'),
    ('USER', 'User'),
    ('PAID_USER', 'Paid User'),
]

class User(models.Model):
    date = models.DateField()
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)  
    role = models.CharField(max_length=10, choices=ROLE_TYPES, null=True, blank=True)

class Conversion(models.Model):
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_parameters = JSONField()

class FileConversion(models.Model):
    date = models.DateField()
    conversion = models.ForeignKey(Conversion, on_delete=models.CASCADE)
    input_file = models.ForeignKey('File', related_name='input_file', on_delete=models.CASCADE)
    output_file = models.ForeignKey('File', related_name='output_file', on_delete=models.CASCADE)

class File(models.Model):
    date = models.DateField()
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    path = models.TextField()
    type = models.TextField()

class Transaction(models.Model):
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
