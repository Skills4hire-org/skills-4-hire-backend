from django.db import models
from django.contrib.auth import get_user_model

import uuid

User = get_user_model()

class Wallet(models.Model):
    wallet_id = models.UUIDField(max_length=20, primary_key=True, default=uuid.uuid4, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")

    main_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    locked_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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

    
