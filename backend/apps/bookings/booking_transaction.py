from .models import BookingTransaction, Bookings

from rest_framework.exceptions import ValidationError

from django.db import transaction
from django.db.models import Q
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

def process_transaction(booking_id: UUID, action, idempotency_key, status: bool):
    
    if action not in BookingTransaction.Type.values:
        raise ValueError("in valid action object")
    
    try:
        booking = Bookings.objects.\
        select_for_update(nowait=True)\
        .select_related("customer", 'provider', 'cancelled_by', 'accepted_by')\
        .get(pk=booking_id)

    except Bookings.DoesNotExist:
        logger.info("can find booking")
        raise ValidationError("booking not found")

    with transaction.atomic():
        try:
            booking_transaction = BookingTransaction(
                booking=booking, sender=booking.customer,
                receiver=booking.provider.profile.user,
                amount=booking.price, platform_fee=booking.platform_fee,
                idempotency_key=idempotency_key
            )
            if action == BookingTransaction.Type.ESCROW_HOLD:
                booking_transaction.type = booking_transaction.Type.ESCROW_HOLD
            elif action == BookingTransaction.Type.REFUND:
                booking_transaction.type = BookingTransaction.Type.REFUND
            elif action == BookingTransaction.Type.RELEASE:
                booking_transaction.type = BookingTransaction.Type.RELEASE
            else:
                raise ValueError()


            if status:
                booking_transaction.status = BookingTransaction.Status.COMPLETED
            else:
                booking_transaction.status = BookingTransaction.Status.FAILED
            
            booking_transaction.save()
        except Exception as exc:
            logger.exception(f"Failed to process booking transaction: {exc}", exc_info=True)
            raise Exception(exc)
    
    return booking_transaction

def transaction_ready_exists(user, idempotency):
    existing = BookingTransaction.objects.filter(
        idempotency_key=idempotency
    ).first()
    
    if existing:
        return True, existing
    return False, None