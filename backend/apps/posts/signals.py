from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import PostLike


@receiver(post_save, sender=PostLike)
def auto_update_notification(sender, created, instance, **kwargs):
    """
    Automatically create or update notification when a PostLike is created.
    """

    pass