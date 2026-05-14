from django.db import models, transaction
from django.conf import settings

import uuid
from django.contrib.postgres.fields import ArrayField

class BaseProfile(models.Model):
    """ 
        A Base User profile for storing all user essential data, both customer and service professionals share this profile
    """
    class GenderChoices(models.TextChoices):
        MALE = "MALE"
        FEMALE = "FEMALE"
        OTHER = "OTHER"
         
    profile_id = models.UUIDField(
        max_length=20,
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
        db_index=True
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")

    gender = models.CharField(choices=GenderChoices.choices, max_length=100, blank=True, db_index=True)
    bio = models.TextField(max_length=10000, blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)

    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    # Trust score: computed from completed jobs, ratings, and endorsements
    # Normalized to 0.0-1.0 range. This is the most important ranking signal.
    trust_score = models.FloatField(default=0.0, db_index=True)
    
    # Location: composite field used for relevance matching in recommendations
    location = models.CharField(max_length=200, blank=True, null=True, help_text="User's primary location for relevance scoring")
    
    # Category interests: stored as JSONField for flexibility in querying
    # Format: {"categories": ["category1", "category2"]} or similar
    category_interest = models.JSONField(default=list, blank=True, help_text="Categories the user engages with for recommendations")
    
    # is_active_user: flag to mark recently active users for feed ranking boost
    is_active_user = models.BooleanField(default=True, db_index=True, help_text="User is actively engaging with the platform")
    
    # last_active: updated on login or post interaction; used to compute is_active_user
    last_active = models.DateTimeField(blank=True, null=True, help_text="Last time user logged in or interacted with content")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True, db_index=True)

    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"BaseProfile({self.display_name} {self.profile_id})"

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=("is_active",), name="is_d_idx"),
            models.Index(fields=("trust_score",), name="trust_score_idx"),
            models.Index(fields=("is_active_user",), name="is_active_user_idx"),
            models.Index(fields=("last_active",), name="last_active_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.user.full_name if self.user.full_name else self.user.first_name
        super().save(*args, **kwargs)

    