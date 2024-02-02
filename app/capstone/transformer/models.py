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


class Product(models.Model):
    name = models.TextField()
    get_display_price_cents = models.IntegerField(default=0) #stored in cents for stripe
    get_display_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    description = models.TextField()
    phrase = models.TextField()
    length_days = models.IntegerField(default=0)

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    has_subscription = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_premium = models.BooleanField(default=False)