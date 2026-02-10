from .utils.pusher_utils import get_pusher_client, ValidationError, _, sync_to_async
from .models import Notification

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from uuid import UUID
UserModel = get_user_model()


async def create_notification(event: str, message: str, user):
    if not isinstance(user, UserModel):
        raise ValidationError(_("Invalid user provided. Expected a UserModel instance."), 
                              code="invalid_user")
    
    try:
        with transaction.atomic():
            await Notification.objects.acreate(user=user, event=event, content=message)
    except Exception as e:
        raise Exception(_(f"Error creating notification service: {str(e)}"))

async def send_push_notification(user_pk: UUID, event: str, data: str):
    user = get_object_or_404(UserModel, pk=user_pk, is_active=True)
    pusher_client = await get_pusher_client()

    try:
        pusher_client.trigger(channels=f"private-user-{user.pk}", event_name=event, data=data)
    except Exception as e:
        raise Exception(_(f"Error when triggerin realtime notification: {str(e)}"))
    
