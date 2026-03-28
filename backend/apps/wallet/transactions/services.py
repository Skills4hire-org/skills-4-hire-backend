from django.db import transaction

from .models import Transactions

import uuid

from ...bookings.models import Bookings
from ...core.utils.py import get_or_none

def get_or_create_transaction(idempotency_key, model, sender, receiver, **validated_data):
    if not isinstance(idempotency_key, uuid.UUID):
        raise ValueError('idempotency_key is not a valid uuid')

    if sender is None or receiver is None:
        raise ValueError("sender and receiver must not be None")
    if model is None:
        raise ValueError("model is not a valid model")
    # check is the instance of this model(Booking or Payment)
    is_booking = bool
    is_payment = bool

    if isinstance(model, Bookings):
        is_booking = True
    else:
        is_payment = True
    try:
        # check is already existing transaction first
        pending_transaction = get_or_none(Transactions,
            idempotency_key=idempotency_key, status=Transactions.Status.PENDING)
        if pending_transaction:
            return pending_transaction
        else:
            # create and return a new transaction
            with transaction.atomic():
                transaction_instance = Transactions(
                    idempotency_key=idempotency_key,
                    sender=sender, receiver=receiver,
                    **validated_data)
                if is_booking:
                    transaction_instance.booking = model
                else:
                    transaction_instance.payment = model
                transaction_instance.save()

        return transaction
    except Exception  as exc:
        raise Exception(exc)






