import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Meetup


@receiver(post_delete, sender=Meetup)
def delete_meetup_image(sender, instance, **kwargs):
    """
    Deletes image file from filesystem
    when corresponding `Meetup` object is deleted.
    """
    if instance.image and instance.image.path:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
