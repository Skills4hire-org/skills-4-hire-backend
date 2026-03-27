from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import Bookings, PaymentRequestBooking
from ..notification.services import send_general_notification
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
        save_notification =   send_general_notification(
            event=event,
            message=message,
            sender=instance.customer,
            receiver=provider
        )
    except Exception as e:
        logger.exception(f"Error sending real-time update: {str(e)}",exc_info=True)

@receiver(signal=post_save, sender=PaymentRequestBooking)
def send_payment_request_update(sender, instance, created, **kwargs):
    if not isinstance(instance, PaymentRequestBooking):
        return
    if not created:
        return

    try:
        customer = instance.customer
        sender = instance.provider.profile.user
        message = f'{sender.full_name} Requested a payout '
        event = NotificationEvents.PAYMENT.value

        send_general_notification(
            sender=sender,
            receiver=customer,
            message=message,
            event=event
        )
    except Exception as e:
        logger.exception(f"Error sending payment request: {str(e)}",exc_info=True)


    