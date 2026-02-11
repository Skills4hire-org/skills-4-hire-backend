from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction, DatabaseError
from django.db.models import F

from .models import Bookings
from .helpers import get_user_wallet
from ..notification.events import NotificationEvents
from ..notification.services import create_notification, send_push_notification


from rest_framework.exceptions import ValidationError

import logging
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

User = get_user_model()

def user_in_booking(user, booking) -> bool:
    return user in (
        booking.customer,
        booking.provider.profile.user
    )
def _cancel_booking(booking, user) -> bool:
    if not isinstance(booking, Bookings) and  not isinstance(user, User):
        raise ValidationError("Failed: 'booking' and 'user' shoul ba valid instances")
    valid_user = user_in_booking(user=user, booking=booking)
    notification_even = NotificationEvents.BOOKING.value
    if valid_user:
        try:
            with transaction.atomic():
                booking.booking_status = Bookings.BookingStatus.CANCELLED
                booking.cancelled_by = user
                booking.cancelled_at = timezone.now()
                booking.save(update_fields=("booking_status", "cancelled_by", "cancelled_at"))
            logger.info(f"Booking {booking.pk} cancelled by user {user.username}.")

            async_to_sync(create_notification)(
                event=notification_even,
                message="Your booking has been cancelled.",
                user=booking.customer
            )
            async_to_sync(send_push_notification)(
                user_pk=booking.customer.pk,
                event=notification_even,
                data={
                    "booking_id": str(booking.pk)
                }
            )
            return True
        except DatabaseError:
            logger.exception(f"Failed to cancel booking {booking.pk} by user {user.username}. Database error occurred.")
            raise DatabaseError("Failed to cancel booking due to a database error.")
        except Exception as e:
            logger.exception(f"Failed to cancel booking {booking.pk} by user {user.username}. Error: {str(e)}")
            raise ValidationError("Failed to cancel booking due to an unexpected error.")
    return False

def _accept_booking(booking, user):
    if not isinstance(booking, Bookings) and  not isinstance(user, User):
        raise ValidationError("Failed: 'booking' and 'user' should ba valid instances")
    customer_wallet = get_user_wallet(user=booking.customer)
    if customer_wallet is None:
        raise ValidationError("User has not wallet instance.")
    if customer_wallet.main_balance < booking.price:
        raise ValidationError("Insufficient balance to pay provider.")
    try:
        with transaction.atomic():
            customer_wallet.main_balance=F("main_balance") - booking.price
            customer_wallet.locked_balance=F("locked_balance") + booking.price
            customer_wallet.save(update_fields=("main_balance", "locked_balance"))
            booking.booking_status = Bookings.BookingStatus.COMPLETED
            booking.save(update_fields=("booking_status",))
            logger.info(f"Booking {booking.pk} accepted by provider {booking.provider.profile.user.username}. \
                        Customer {booking.customer.username} wallet debited by {booking.price}.")
            

            async_to_sync(create_notification)(
                event=NotificationEvents.PAYMENT.value,
                message="Your payment has been processed successfully.",
                user=booking.customer,
            )

            async_to_sync(create_notification)(
                event=NotificationEvents.BOOKING.value,
                message="Your booking has been accepted.",
                user=booking.customer,
            )
            async_to_sync(send_push_notification)(
                user_pk=booking.customer.pk,
                event=NotificationEvents.BOOKING.value,
                data={
                    "booking_id": str(booking.pk)
                }
            )
            
            async_to_sync(send_push_notification)(
                user_pk=booking.customer.pk,
                event=NotificationEvents.PAYMENT.value,
                data={
                    "booking_id": str(booking.pk),
                    "amount": str(booking.price)
                }
            )
            logger.info(f"Booking {booking.pk} accepted by provider {booking.provider.profile.user.username}.")
            return True
    except DatabaseError:
        logger.exception(f"Failed to accept booking {booking.pk} by provider {booking.provider.profile.user.username}. Database error occurred.")
        raise DatabaseError("Failed to accept booking due to a database error.")
    except Exception as e:
        logger.exception(f"Failed to accept booking {booking.pk} by provider {booking.provider.profile.user.username}. Error: {str(e)}")
        raise ValidationError("Failed to accept booking due to an unexpected error.")


    
    
