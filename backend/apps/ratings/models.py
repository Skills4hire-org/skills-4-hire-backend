from django.db import models
from django.contrib.auth import get_user_model

from django.core.validators import MinValueValidator, MaxValueValidator

from ..users.provider_models import ProviderModel

import uuid
import logging


logger = logging.getLogger(__name__)
UserModel = get_user_model()

class ProfileReview(models.Model):
    """ Profile review for skilled professionals """
    review_id = models.UUIDField(
        max_length=20,
        primary_key=True,
        default=uuid.uuid4,
        db_index=True
    )

    provider_profile = models.ForeignKey(
        ProviderModel, on_delete=models.CASCADE,
        related_name="reviews", null=True, blank=True
    )

    reviewed_by = models.ForeignKey(
        UserModel, on_delete=models.SET_NULL,
        related_name="reviews", null=True
    )

    ratings = models.PositiveIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(5)
    ], blank=True, null=True)

    reviews = models.TextField(null=True, blank=True, max_length=1000)

    is_active = models.BooleanField(default=True)

    # Timestamp 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ratings_review"
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"], name="active_deleted_idx"),
            models.Index(fields=["created_at"], name="d_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=['reviewed_by', 'provider_profile'], name="unique_user_profile"),
        ]
    def __str__(self):
        return f"Review {self.review_id}  created: {self.created_at}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def soft_delete(self):
        if hasattr(self, "is_active"):
            setattr(self, "is_active", False)

        self.save(update_fields=['is_active'])