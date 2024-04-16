from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, File
import os


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs) -> None:  # type: ignore
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs) -> None:  # type: ignore
    instance.profile.save()


@receiver(pre_delete, sender=User)
def delete_related_data(sender, instance, **kwargs):  # type: ignore
    print("DELETING")

    # delete profile picture from filesystem
    try:
        if hasattr(instance, "profile"):
            instance.profile.delete()
    except Profile.DoesNotExist:
        pass

    # delete user files from filesystem
    # retrieve input file objects related to the user
    user_files = File.objects.filter(user=instance)
    # loop through each file object, delete the actual file from the filesystem
    for file_obj in user_files:
        if file_obj.file:
            try:
                # construct the full path to the file
                file_path = file_obj.file.path
                # check if file exists on the filesystem and delete it
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                # Handle potential exceptions, e.g., file not found
                print(f"Error deleting file {file_path}: {e}")
    # After deleting the files from the filesystem, delete the File objects from the database
    user_files.delete()
