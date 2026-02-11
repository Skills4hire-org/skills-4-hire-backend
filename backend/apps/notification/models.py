from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

import uuid

UserModel = get_user_model()

class Notification(models.Model):
    notification_id = models.UUIDField(max_length=20, primary_key=True, unique=True, default=uuid.uuid4)

    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="notifications")
    event = models.CharField(max_length=200, null=True, blank=True)
    content = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = ("Notification")
        verbose_name_plural = ("Notifications")

        indexes = [
            models.Index(fields=['is_deleted'], name='deletedat_idx'),
            models.Index(fields=["is_read"], name="readat_idx"),
            models.Index(fields=['notification_id'], name="notification_idx")
        ]
    
    def __str__(self):
        return "Notification Service ({}, {})".format(self.user.email, self.event)
    
    def mark_as_read(self):
        setattr(self, "is_read", True)
        setattr(self, "read_at", timezone.now())
        with transaction.atomic():
            self.save(update_fields=["is_read", "read_at"])

    def delete(self):
        setattr(self, "is_deleted", True)
        with transaction.atomic():
            self.save(update_fields="is_deleted")