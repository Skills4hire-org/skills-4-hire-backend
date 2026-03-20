from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import Message, Negotiations
from ..notification.services import send_general_notification
from ..notification.events import NotificationEvents
from .core.utils import  trigger_notification
from apps.core.utils.py import log_action


import logging

logger = logging.getLogger(__name__)


@receiver(signal=post_save, sender=Message)
def send_real_time_to_receiver(sender, created, instance, **kwargs):

    if not isinstance(instance, Message):
        return
    if not created:
        return

    event = NotificationEvents.MESSAGE.value
    sender = instance.sender
    message = f"{sender.full_name} sent you a new message!"
    other_receiver = instance.receipient
    if other_receiver is None:
        return
    try:

        send_general_notification(
            sender=sender,
            receiver=other_receiver,
            message=message,
            event=event
        )
        log_action(
            "send_websocket_notification",
            other_receiver,
            {"message": message}
        )
    except Exception as e:
        logger.exception(f"Exception sending notification: {e}", exc_info=True)

@receiver(signal=post_save, sender=Negotiations)
def propose_negotiation(sender, created, instance, **kwargs):
    if not created:
        return
    if not isinstance(instance, Negotiations):
        return

    sender = instance.sender
    other_receiver  = instance.receipient
    if other_receiver is None:
        return

    trigger_notification(instance.status, sender, other_receiver)
    log_action(
        "send_notification",
        other_receiver,
        {"notification": instance.status}
    )




