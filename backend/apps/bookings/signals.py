from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import Bookings
from ..notification.services import send_push_notification, create_notification
from ..notification.events import NotificationEvents

import logging

logger = logging.getLogger(__name__)

@receiver(signal=post_save, sender=Bookings)
async def send_real_time_updates_to_providers(sender, instance: Bookings, created: bool, **kwargs):
    if not created:
        logger.error("")
        return 
    if not isinstance(instance, Bookings):
        return 
    provider_profile = getattr(instance, "provider")
    if provider_profile is None:
        return 
    user_instance = getattr(provider_profile.profile, "user")
    if user_instance is None:
        return 
    
    event = NotificationEvents.BOOKING.value,
    try:
        save_notification = await create_notification(
            event=event,
            message="You have a new booking request.",
            user=user_instance
        )

        await send_push_notification(
            user_pk=user_instance.pk,
            event=event,
            data={
                "booking_id": instance.pk
            }
        )
    except Exception as e:
        logger.exception(f"Error sending real-time update: {str(e)}",exc_info=True)

    

    