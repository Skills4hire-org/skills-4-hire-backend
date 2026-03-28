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
            locked_total=models.Sum('amounts')
        )
        return current_balance + locked_amounts['locked_total']


class LockedWallet(models.Model):
    locked_id = models.UUIDField(
        primary_key=True,unique=True,
        editable=False, default=uuid.uuid4
    )
    booking = models.OneToOneField(Bookings, on_delete=models.CASCADE, related_name="locked")
    user_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='locked_balance')

    is_released = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

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