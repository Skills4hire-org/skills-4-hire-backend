from django.db import models
from django.conf import settings

import uuid

# referral models

UserModel = settings.AUTH_USER_MODEL

class ReferralCode(models.Model):
    referral_code_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(
        UserModel,
        on_delete=models.CASCADE,
        related_name="referral_code"
    )
    code = models.CharField(max_length=16, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} ({self.owner.email})"


class Referral(models.Model):
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"       
        REWARDED = "rewarded", "Rewarded"
        CONVERTED = "converted", "Converted"     

    referral_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referrer = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="referrals_made"
    )
    referred = models.OneToOneField(
        UserModel,
        on_delete=models.CASCADE,
        related_name="referral_record"
    )
    code_used = models.ForeignKey(
        ReferralCode,
        on_delete=models.SET_NULL,
        null=True,
        related_name="referrals"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    rewarded_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["referrer", "status"]),
            models.Index(fields=["referred"]),
        ]

    def __str__(self):
        return f"{self.referrer.email} → {self.referred.email} [{self.status}]"
        
class ReferralTransactions(models.Model):

    class Status(models.TextChoices):
        PENDING = 'PENDING'
        COMPLETED = 'COMPLETED'
        FAILED = 'FAILED'
        REVERSED = 'REVERSED'

    transaction_id = models.UUIDField(
        primary_key=True, editable=False, unique=True,
        db_index=True, default=uuid.uuid4
    )

    amount = models.DecimalField(decimal_places=2, max_digits=8, blank=False, null=False)
    status = models.CharField(choices=Status.choices, default=Status.PENDING, max_length=50)

    reference_key = models.CharField(max_length=255, null=False, unique=True)
    idempotency_key = models.UUIDField(max_length=255, null=False, blank=False)
    transfer_code = models.CharField(max_length=255, null=True, blank=True)
    
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="referral_transactions")
    referrals = models.ManyToManyField(Referral, related_name="referrals")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
    reversed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f" Referral Transactions | {self.user.full_name} | {self.status} | {self.amount}"
    
    class Meta:
        verbose_name = "Referral_transaction"
        indexes = [
            models.Index(
                fields=['status']
            ),
            models.Index(
                fields=['reference_key']
            ),
            models.Index(
                fields=['idempotency_key']
            ),
            models.Index(
                fields=['created_at']
            ),
            models.Index(
                fields=['is_active']
            )
        ]