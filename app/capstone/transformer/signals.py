from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, Conversion, File, Transaction, Subscription


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs) -> None:  # type: ignore
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs) -> None:  # type: ignore
    instance.profile.save()


@receiver(post_delete, sender=User)
def delete_related_data(sender, instance, **kwargs):  # type: ignore
    Conversion.objects.filter(user=instance).delete()
    File.objects.filter(user=instance).delete()
    Transaction.objects.filter(user=instance).delete()
    Subscription.objects.filter(user=instance).delete()
