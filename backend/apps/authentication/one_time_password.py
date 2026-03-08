from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone

User = getattr(settings, "AUTH_USER_MODEL")

class OneTimePassword(models.Model):
    otp_id = models.UUIDField(
        max_length=20, 
        unique=True,
        primary_key=True,
        db_index=True,
        default=uuid.uuid4
        )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="one_time_codes")
    hash_code = models.CharField(max_length=100, unique=True, db_index=True, null=False)
    raw_code = models.CharField(max_length=100, unique=True, db_index=True, null=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_used = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"OneTimePassword({self.user.email}, {self.raw_code})"

    def is_expired(self) -> bool:
        expiry_minute = getattr(settings, "OTP_EXPIRY", 15)   
        expires_at = self.created_at + timezone.timedelta(minutes=expiry_minute)
        if timezone.now() > expires_at:
            return True
        return False
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "hash_code", "raw_code"], name="unique_code_user")
        ]

        indexes = [
            models.Index(fields=["hash_code"], name="hash_cde_idx"),
            models.Index(fields=["is_active", "is_used"], name='active_used_idx')
        ]
        
        verbose_name = "OneTimePassword"
        ordering = ["-created_at"]


        


