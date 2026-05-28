from rest_framework.exceptions import ValidationError

from .models import Notification

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.shortcuts import get_object_or_404

import logging

logger = logging.getLogger(__name__)
UserModel = get_user_model()


def create_notification(event: str, message: str, sender, receiver):
    try:
        with transaction.atomic():
            sender = get_object_or_404(UserModel, user_id=sender)
            receiver = get_object_or_404(UserModel, user_id=receiver)
            Notification.objects.create(sender=sender, receiver=receiver, event=event, content=message)
            logger.info(f"Notification created for user {receiver.email} with event {event}")
    except Exception as e:
        logger.exception(f"Error creating notification: {str(e)}", exc_info=True)
        raise Exception(_(f"Error creating notification service: {str(e)}"))