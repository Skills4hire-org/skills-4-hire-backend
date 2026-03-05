from celery.bin.events import events
from django.dispatch import receiver
from django.db.models.signals import post_save
from pyexpat.errors import messages

from .models import PostLike, Comment
from apps.notification.services import send_general_notification
from apps.notification.events import NotificationEvents

from asyncio.log import  logger

@receiver(post_save, sender=PostLike)
def send_realtime_notif_on_like(sender, created, instance, **kwargs):
    """
    Automatically create or update notification when a PostLike is created.
    """
    if not created:
        return
    if not isinstance(instance, PostLike):
        return

    event = NotificationEvents.SYSTEM.value
    received_by = instance.post.user
    sender = instance.user
    notification_message = f"{sender.username} Liked Your Post"

    try:
        send_general_notification(
            sender=sender,
            receiver=received_by,
            event=event,
            message=notification_message
        )
    except Exception as e:
        (logger.error(e))

@receiver(signal=post_save, sender=Comment)
def auto_send_realtime_notif_on_comment(sender, created, instance, **kwargs):
    if not created:
        return

    if not isinstance(instance, Comment):
        return

    sender = instance.user
    received_by = instance.post.user

    event = NotificationEvents.SYSTEM.value

    comment_message = f"{sender.username} Commented On Your Post"

    try:
        send_general_notification(
            sender=sender,
            event=event,
            receiver=received_by,
            message=comment_message
        )
    except Exception as e:
        logger.error(e)
        return