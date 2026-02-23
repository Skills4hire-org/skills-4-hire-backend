from rest_framework.exceptions import ValidationError

from .models import Notification

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from channels.layers import get_channel_layer

from uuid import UUID
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)
UserModel = get_user_model()

def create_notification(event: str, message: str, sender, receiver):
    if not isinstance(sender, UserModel):
        raise ValidationError(_("Invalid sender provided. Expected a UserModel instance."), 
                              code="invalid_sender")
    if not isinstance(receiver, UserModel):
        raise ValidationError(_("Invalid receiver provided. Expected a UserModel instance."), 
                              code="invalid_receiver")
    
    try:
        with transaction.atomic():
            Notification.objects.create(sender=sender, receiver=receiver, event=event, content=message)
            logger.info(f"Notification created for user {receiver.email} with event {event}")
    except Exception as e:
        logger.exception(f"Error creating notification: {str(e)}", exc_info=True)
        raise Exception(_(f"Error creating notification service: {str(e)}"))

def trigger_notification(user_pk, message):
    if user_pk is None or message is None:
        raise ValidationError("Missing required field to  trigger notification")

    try:
        channel_layer = get_channel_layer()
        group_name = f"user_{user_pk}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notifications",
                "message": message
            }
        )
    except Exception as e:
        logger.exception(f"Error trying to trigger notifications.. {e}")
        raise Exception(f"Error {e}")