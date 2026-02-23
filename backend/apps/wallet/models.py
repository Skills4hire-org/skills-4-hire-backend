from django.db import models
from django.contrib.auth import get_user_model

import uuid
from decimal import Decimal

from apps.users.provider_models import ProviderModel

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
    def main_balance(self):
        overrall_balance = self.balance
        locked_balance = self.locked_wallet.all().only("amount")
        locked_amount = Decimal()
        for data in locked_balance:
            locked = data.amount
            locked_amount += locked
        
        balance = overrall_balance - locked_amount
        return balance
        



class LockedWallet(models.Model):
    locked_wallet_id = models.UUIDField(max_length=20, primary_key=True, default=uuid.uuid4, unique=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="locked_wallet")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    provider = models.ForeignKey(ProviderModel, on_delete=models.CASCADE, related_name="locked_wallet", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Locked Wallet {self.locked_wallet_id} for Wallet {self.wallet.wallet_id}"

    class Meta:
        verbose_name = "locked_wallets"
        constraints = [
            models.UniqueConstraint(fields=("locked_wallet_id", "wallet"), name="unique_locked_wallet"),
            models.UniqueConstraint(fields=("wallet", "provider"), name="unique_wallet_provider_lock")
        ]
        indexes = [
            models.Index(fields=["locked_wallet_id",], name="locked_wallet_id"),
            models.Index(fields=["wallet"], name="wallet_idx"),
            models.Index(fields=["provider"], name="prov_idx")
        ]
    
