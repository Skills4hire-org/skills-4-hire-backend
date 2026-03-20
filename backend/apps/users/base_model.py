from django.db import models, transaction
from django.conf import settings

import uuid

class BaseProfile(models.Model):
    """ 
        A Base User profile for storing all user essential data, both customer and service professionals share this profile
    """
    class GenderChoices(models.TextChoices):
         MALE = "MALE", "Male"
         FEMALE = "FEMALE", "Female"
         OTHER = "OTHER", "Other"
         

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
        ]

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.user.full_name if self.user.full_name else self.user.first_name
        super().save(*args, **kwargs)

    