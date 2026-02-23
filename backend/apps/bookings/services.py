from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction, DatabaseError
from django.db.models import F, Q

from .models import Bookings, ProviderModel
from ..notification.events import NotificationEvents
from ..notification.services import create_notification, trigger_notification
from apps.wallet.services import WalletService
from .helpers import can_delete_booking


from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from asyncio.log import logger

User = get_user_model()

class BookingService:

    @staticmethod
    def cancel_booking(booking, user) -> bool:
        if not isinstance(booking, Bookings) and  not isinstance(user, User):
            raise ValidationError("Failed: 'booking' and 'user' should ba valid instances")
        notification_event = NotificationEvents.BOOKING.value
        message = f"Your booking has been cancelled by {user.username}."
        try:
            booking.cancel_booking(user=user)
            logger.info(f"Booking {booking.pk} cancelled by user {user.username}.")

            create_notification(
                event=notification_event,
                message=message,
                sender=user,
                receiver=booking.provider.profile.user if user == booking.customer else booking.customer
            )
            trigger_notification(
                user_pk=booking.customer.pk,
                message=message,
            )
            return True
        except DatabaseError:
            logger.exception(f"Failed to cancel booking {booking.pk} by user {user.username}. Database error occurred.")
            raise DatabaseError("Failed to cancel booking due to a database error.")
        except Exception as e:
            logger.exception(f"Failed to cancel booking {booking.pk} by user {user.username}. Error: {str(e)}")
            raise ValidationError("Failed to cancel booking due to an unexpected error.", e)

    @staticmethod
    def accept_booking(booking, user):
        if not isinstance(booking, Bookings) and  not isinstance(user, User):
            raise ValidationError("Failed: 'booking' and 'user' should ba valid instances")
        customer_wallet = WalletService.get_user_wallet(user=booking.customer)

        if customer_wallet.main_balance < booking.price:
            raise ValidationError("Insufficient balance to pay provider.")
        try:
            with transaction.atomic():
                WalletService.lock_booking_payment(
                    customer_wallet=customer_wallet, 
                    amount=booking.price,
                    booking=booking)
                booking.accept_booking(user=user)
                logger.info(f"Booking {booking.pk} accepted by provider {booking.provider.profile.user.username}. \
                            Customer {booking.customer.username} wallet debited by {booking.price}.")
                

                payment_message = f"Your payment of {booking.price} has been processed successfully for booking {booking.pk}."
                create_notification(
                    event=NotificationEvents.PAYMENT.value,
                    message=payment_message,
                    sender=booking.customer,
                    receiver=booking.customer
                )

                booking_message = f"Your booking has been accepted by {booking.provider.profile.user.username}."
                create_notification(
                    event=NotificationEvents.BOOKING.value,
                    message=booking_message,
                    sender=booking.provider.profile.user,
                    receiver=booking.customer
                )
                trigger_notification(
                    user_pk=booking.customer.pk,
                    message=booking_message,
                )
                
                trigger_notification(
                    user_pk=booking.customer.pk,
                    message=payment_message,
                )
                logger.info(f"Booking {booking.pk} accepted by provider {booking.provider.profile.user.username}.")
                return True
        except DatabaseError:
            logger.exception(f"Failed to accept booking {booking.pk} by provider {booking.provider.profile.user.username}. Database error occurred.")
            raise DatabaseError("Failed to accept booking due to a database error.")
        except Exception as e:
            logger.exception(f"Failed to accept booking {booking.pk} by provider {booking.provider.profile.user.username}. Error: {str(e)}")
            raise ValidationError(f"Failed to accept booking due to an unexpected error: {str(e)}")

    @staticmethod
    def customer_and_provider_view(user, queryset):
        if queryset is None:
            return 0
        try:
            provider_profile = ProviderModel.objects.get(profile=user.profile)
            queryset = queryset.filter(provider=provider_profile)
        except ProviderModel.DoesNotExist:
            queryset = queryset.filter(customer=user)
        return queryset
    
    @staticmethod
    def delete_booking(booking, user):
        if not can_delete_booking(user, booking):
            raise PermissionDenied()
        booking.soft_delete()
        return booking

        


        
        
