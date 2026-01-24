from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction, DatabaseError
from django.db.models import F

from .models import Bookings
from .helpers import get_user_wallet

from rest_framework.exceptions import ValidationError

User = get_user_model()

def _is_booking_user(user, booking) -> bool:
    return user in (
        booking.customer,
        booking.provider.profile.user
    )
def _cancel_booking(booking, user) -> bool:
    if not isinstance(booking, Bookings) and  not isinstance(user, User):
        raise ValidationError("Failed: 'booking' and 'user' shoul ba valid instances")
    valid_user = _is_booking_user(user=user, booking=booking)
    if valid_user:
        try:
            with transaction.atomic():
                booking.booking_status = Bookings.BookingStatus.CANCELLED
                booking.cancelled_by = user
                booking.cancelled_at = timezone.now()
            booking.save(update_fields=("booking_status", "cancelled_by", "cancelled_at"))
        except DatabaseError:
            raise 
        return True
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
            wallet_update = customer_wallet.update(
                main_balance=F("main_balance") - booking.price, 
                locked_balance=F("locked_balance") + booking.price
                )
            if wallet_update == 0:
                raise ValidationError("Failed to debit customer wallet.")
            booking.booking_status = Bookings.BookingStatus.COMPLETED
            booking.save(update_fields=("booking_status",))
            return True
    except DatabaseError:
        raise


    
    
