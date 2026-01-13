from django.db import models
from django.conf import settings
from django.db.models import F
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from ..users.base_model import BaseProfile

import uuid
import logging

logger = logging.getLogger(__name__)

class ProfileReview(models.Model):
    review_id = models.UUIDField(
        max_length=20,
        primary_key=True,
        default=uuid.uuid4,
        db_index=True
    )

    profile = models.ForeignKey(BaseProfile, on_delete=models.CASCADE, related_name="reviews")
    reviewed_by = models.ForeignKey(getattr(settings, "AUTH_USER_MODEL"), on_delete=models.SET_NULL, related_name="reviews", null=True)

    review = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    # Timestamp 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "is_deleted"], name="active_deleted_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["reviewed_by", "profile"], name="unique_review_profile")
        ]
    def __str__(self):
        return f"Review {self.review_id} for Profile {self.profile.profile_id}"


    def soft_delete(self):
        if not hasattr(self, "is_active") or not hasattr(self, "is_deleted"):
            logger.error(f"soft_delete called on ProfileReview {self.review_id} but required fields are missing.")
            return
        
        self.is_active=~F("is_active")
        self.is_deleted=~F("is_deleted")
        self.deleted_at=F("deleted_at") if self.deleted_at else timezone.now()
        self.save(update_fields=["is_active", "is_deleted", "deleted_at"])

    def can_edit(self, user):
        if self.reviewed_by == user:
            return True
        if user.is_admin:
            return True
        return False

class ProfileRating(models.Model):
    rating_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        max_length=20,
        db_index=True
    )

    profile = models.ForeignKey(BaseProfile, on_delete=models.CASCADE, related_name="ratings")
    rate_by = models.ForeignKey(getattr(settings,  "AUTH_USER_MODEL"), on_delete=models.SET_NULL, null=True, related_name="ratings")

    rating = models.PositiveIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(5)
    ])

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)


    def soft_delete(self):
        if not hasattr(self, "is_active") or not hasattr(self, "is_deleted"):
            logger.error(f"soft_delete called on ProfileReview {self.review_id} but required fields are missing.")
            return
        
        self.is_active=~F("is_active")
        self.is_deleted=~F("is_deleted")
        self.deleted_at=F("deleted_at") if self.deleted_at else timezone.now()
        self.save(update_fields=["is_active", "is_deleted", "deleted_at"])
    
    def can_edit(self, user):
        if self.rate_by == user:
            return True
        if user.is_admin:
            return True
        return False
    
    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(fields=("rate_by", "profile"), name="unique_rate_profile")
        ]
        indexes = [
            models.Index(fields=["is_active", "is_deleted"], name="active_delete_idx"),
        ]