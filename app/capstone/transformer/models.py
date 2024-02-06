from django.db import models
from django.utils import timezone
from django.db.models import JSONField
from django.contrib.auth.models import User
from PIL import Image


class Conversion(models.Model):
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    user_parameters = JSONField(null=True)


class File(models.Model):
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    conversion = models.ForeignKey(Conversion, on_delete=models.CASCADE)
    is_output = models.BooleanField(default=False)
    is_input = models.BooleanField(default=False)
    type = models.TextField()
    file = models.FileField(upload_to="", max_length=500)


class Transaction(models.Model):
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()


class Products(models.Model):
    name = models.TextField()
    get_display_number = models.IntegerField()
    get_display_price = models.FloatField()
    description = models.TextField()
    phrase = models.TextField()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default="default_pfp.jpg", upload_to="profile_pics")

    def __str__(self):
        return f"{self.user.username} Profile"

    # Override the save method of the model
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)  # Open image

        # resize image
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)  # Resize image
            img.save(self.image.path)  # Save it again and override the larger image
