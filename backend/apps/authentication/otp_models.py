from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

User = getattr(settings, "AUTH_USER_MODEL")

class OTP_Base(models.Model):
    otp_id = models.UUIDField(
        max_length=20, 
        unique=True,
        primary_key=True,
        db_index=True,
        default=uuid.uuid4
        )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="codes")
    code = models.CharField(max_length=100, unique=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"OTP_Base({self.user.email}, {self.code})"

    def is_expired(self) -> bool:
        expiry_minute = getattr(settings, "OTP_EXPIRY", 15)   
        expires_at = self.created_at + timezone.timedelta(minutes=expiry_minute)
        if timezone.now() > expires_at:
            return True
        return False


        


