from .utils.pusher_utils import get_pusher_client, ValidationError, _, sync_to_async
from .models import Notification

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from uuid import UUID
import logging

logger = logging.getLogger(__name__)
UserModel = get_user_model()

@sync_to_async
def create_notification(event: str, message: str, user):
    if not isinstance(user, UserModel):
        raise ValidationError(_("Invalid user provided. Expected a UserModel instance."), 
                              code="invalid_user")
    
    try:
        with transaction.atomic():
            Notification.objects.create(user=user, event=event, content=message)
            logger.info(f"Notification created for user {user.email} with event {event}")
    except Exception as e:
        logger.exception(f"Error creating notification: {str(e)}", exc_info=True)
        raise Exception(_(f"Error creating notification service: {str(e)}"))

@sync_to_async
def send_push_notification(user_pk: UUID, event: str, data: str):
    user = get_object_or_404(UserModel, pk=user_pk, is_active=True)
    pusher_client = get_pusher_client()

    try:
        pusher_client.trigger(channels=f"private-user-{user.pk}", event_name=event, data=data)
        logger.info(f"Push notification sent to user {user.email} for event {event}")
    except Exception as e:
        logger.exception(f"Error sending push notification: {str(e)}", exc_info=True)
        raise Exception(_(f"Error when triggering realtime notification: {str(e)}"))
    
