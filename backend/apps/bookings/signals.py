from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import Bookings
from ..notification.services import create_notification, trigger_notification
from ..notification.events import NotificationEvents

import logging

logger = logging.getLogger(__name__)

@receiver(signal=post_save, sender=Bookings)
def send_real_time_updates_to_providers(sender, instance: Bookings, created: bool, **kwargs):
    if not created:
        logger.error("")
        return 
    if not isinstance(instance, Bookings):
        return 
    provider_profile = getattr(instance, "provider")
    if provider_profile is None:
        return 
    provider = getattr(provider_profile.profile, "user")
    if provider is None:
        return 
    
    event = NotificationEvents.BOOKING.value
    customer_name = instance.customer.username if \
                    instance.customer.username else instance.customer.full_name
    try:
        message = f"{customer_name.title()} sent you a new booking request."
        save_notification =   create_notification(
            event=event,
            message=message,
            sender=instance.customer,
            receiver=provider
        )

        
        trigger_notification(
            user_pk=provider.pk,
            message=message,
        )
    except Exception as e:
        logger.exception(f"Error sending real-time update: {str(e)}",exc_info=True)

    

    