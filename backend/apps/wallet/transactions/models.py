from django.db import models
from django.contrib.auth import  get_user_model

import uuid

from apps.bookings.models import Bookings

UserModel = get_user_model()


class ActiveTransaction(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class Transactions(models.Model):

    objects = models.Manager()
    is_active_objects = ActiveTransaction()

    transaction_id = models.UUIDField(
        primary_key=True, unique=True,
        db_index=True, editable=False,default=uuid.uuid4
    )
    class Type(models.TextChoices):
        ESCROW_HOLD = 'ESCROW_HOLD'
        RELEASE = 'RELEASE'
        REFUND = 'REFUND'
        DEPOSIT = 'DEPOSIT'
        WITHDRAW = 'WITHDRAW'

    class Status(models.TextChoices):
        PENDING = 'PENDING'
        COMPLETED = 'COMPLETED'
        FAILED = 'FAILED'

    booking = models.ForeignKey(Bookings, on_delete=models.SET_NULL, null=True, related_name='bookings_transactions')

    sender = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='transaction_sender')
    receiver = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='transaction_receiver')
    amount = models.DecimalField(decimal_places=2, max_digits=8)

    type = models.CharField(max_length=20, choices=Type.choices, default=Type.ESCROW_HOLD)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    idempotency_key = models.CharField(max_length=20, null=False, blank=True)
    reference_key = models.CharField(max_length=20, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    transaction_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Transaction{self.transaction_id}"

    class Meta:
        verbose_name = "Transactions"
        indexes = [
            models.Index(fields=['amount']),
            models.Index(fields=['status']),
            models.Index(fields=['type']),
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['reference_key'])
        ]

