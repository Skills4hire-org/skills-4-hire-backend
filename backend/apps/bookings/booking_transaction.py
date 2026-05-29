from .models import BookingTransaction, Bookings

from rest_framework.exceptions import ValidationError

from django.db import transaction
from django.db.models import Q
from uuid import UUID
import logging

from ..notification.consumers import broadcast_notification

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

        is_credit = None
        is_debit = None
        sender = None
        receiver = None
        try:
            booking_transaction = BookingTransaction.objects.create(
                booking=booking,amount=booking.price, platform_fee=booking.platform_fee,
                idempotency_key=idempotency_key, sender=booking.customer,
                receiver=booking.provider.profile.user
            )
            if action == BookingTransaction.Type.ESCROW_HOLD:
                booking_transaction.type = booking_transaction.Type.ESCROW_HOLD
                is_debit = True
                sender = booking_transaction.sender
                receiver = booking_transaction.sender
            elif action == BookingTransaction.Type.REFUND:
                booking_transaction.type = BookingTransaction.Type.REFUND
                is_credit = True
                sender = booking_transaction.sender
                receiver = booking_transaction.sender

            elif action == BookingTransaction.Type.RELEASE:
                booking_transaction.type = BookingTransaction.Type.RELEASE
                is_credit = True
                sender = booking_transaction.sender
                receiver = booking_transaction.receiver
            else:
                raise ValueError()

            if status:
                booking_transaction.status = BookingTransaction.Status.COMPLETED
            else:
                booking_transaction.status = BookingTransaction.Status.FAILED
            
            booking_transaction.save()

            if is_credit:
                broadcast_notification("booking_credit", {
                    "sender": sender, "receiver": receiver, 
                    "amount": booking_transaction.amount, "is_credit": is_credit,
                    "is_debit": is_debit
                })
            if is_debit:
                broadcast_notification("booking_debit", {
                    "sender": sender, "receiver": receiver, "amount": booking_transaction.amount,
                    "is_credit": is_credit, "is_debit": is_debit
                })
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