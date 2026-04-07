from django.db import models
from django.contrib.auth import get_user_model

import uuid
from decimal import Decimal

from apps.users.provider_models import ProviderModel
from ..bookings.models import Bookings

User = get_user_model()

class Wallet(models.Model):
    wallet_id = models.UUIDField(max_length=20, primary_key=True, default=uuid.uuid4, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wallet {self.wallet_id} for User {self.user.username}"

    class Meta:
        verbose_name = "wallets"
        constraints = [
            models.UniqueConstraint(fields=("wallet_id", "user"), name="unique_user_wallet")
        ]
        indexes = [
            models.Index(fields=["wallet_id"], name="pk_idx")
        ]

    @property
    def get_total_balance(self):

        current_balance = self.balance
        locked_amounts = self.locked_balance.filter(is_released=False).aggregate(
            locked_total=models.Sum('amount')
        )

        if locked_amounts['locked_total'] is None:
            return current_balance
        
        return current_balance + locked_amounts['locked_total']

    @property
    def locked_wallet(self):
        "return the total amount for this locked wallet"
        locked_amounts = self.locked_balance.filter(is_released=False).aggregate(
            locked_total=models.Sum('amount')
        )

        if locked_amounts['locked_total'] is None:
            return "0.00"
        return str(locked_amounts['locked_total'])

class LockedWallet(models.Model):
    locked_id = models.UUIDField(
        primary_key=True,unique=True,
        editable=False, default=uuid.uuid4
    )
    booking = models.OneToOneField(Bookings, on_delete=models.CASCADE, related_name="locked")
    user_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='locked_balance')

    is_released = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    mutable_amount = models.DecimalField(max_digits=8, decimal_places=2) # amount with deducted percentages

    locked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Locked Wallet ({self.locked_at}"

    class Meta:
        verbose_name = "Locked Amount"
        indexes = [
            models.Index(fields=('is_released',)),
            models.Index(fields=('locked_at',)),
            models.Index(fields=('user_wallet',)),
            models.Index(fields=('amount',))
        ]

        constraints = [
            models.UniqueConstraint(fields=("booking", 'user_wallet'), name='unique_wallet')
        ]

class ActiveTransaction(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class WalletTransaction(models.Model):

    objects = models.Manager()
    is_active_objects = ActiveTransaction()

    transaction_id = models.UUIDField(
        primary_key=True, unique=True,
        db_index=True, editable=False,default=uuid.uuid4
    )
    class Type(models.TextChoices):
        DEPOSIT = 'DEPOSIT'
        WITHDRAW = 'WITHDRAW'

    class Status(models.TextChoices):
        PENDING = 'PENDING'
        PROCESSING = 'PROCESSING'
        COMPLETED = 'COMPLETED'
        FAILED = 'FAILED'

    amount = models.DecimalField(decimal_places=2, max_digits=8)
    
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, 
        related_name="wallet_transactions"
        )
    
    wallet = models.ForeignKey(
        Wallet, on_delete=models.PROTECT, 
        related_name='wallet_transactions'
        )


    type = models.CharField(max_length=20, choices=Type.choices, default=None)

    status = models.CharField(
        max_length=20, choices=Status.choices, 
        default=Status.PENDING
        )
    
    idempotency_key = models.CharField(max_length=50, null=False, blank=False)
    reference_key = models.CharField(max_length=50, null=False, blank=True)

    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    reasons = models.TextField(null=True)

    transaction_date = models.DateField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wallet Transaction {self.transaction_id} | {self.user.email} | {self.amount} | {self.status}"

    @property
    def reference_str(self):
        """Paystack expects a string reference, not a UUID object."""
        return str(self.reference_key)

    class Meta:
        verbose_name = "Wallet Transaction"
        indexes = [
            models.Index(fields=['amount']),
            models.Index(fields=['status']),
            models.Index(fields=['type']),
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['reference_key'])
        ]

class WebhookEvent(models.Model):
    """Idempotency guard — one row per Paystack event reference."""

    class Status(models.TextChoices):
        RECEIVED   = "received",   "Received"
        PROCESSING = "processing", "Processing"
        PROCESSED  = "processed",  "Processed"
        FAILED     = "failed",     "Failed"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference   = models.CharField(max_length=200, unique=True, db_index=True)
    event_type  = models.CharField(max_length=100)
    payload     = models.JSONField()
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    error       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_type} | {self.reference} | {self.status}"
