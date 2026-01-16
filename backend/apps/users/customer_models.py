from django.db import models
from django_countries.fields import CountryField
import uuid

from .base_model import BaseProfile

class CustomerModel(models.Model):

    customer_id = models.UUIDField(
        max_length=20, 
        primary_key=True,
        default=uuid.uuid4,
        unique=True, 
        db_index=True
    )

    profile = models.OneToOneField(BaseProfile, on_delete=models.CASCADE, related_name="customer_profile")

    website = models.URLField(blank=True)
    country = CountryField(blank=True, null=True)

    industry = models.URLField(blank=True, null=True)
    total_hires  = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=("is_active", "is_deleted"), name="dele_acti_idx"),
            models.Index(fields=("is_active", "is_deleted", "is_verified"), name="very_dele_acti_idx")
        ]

    def __str__(self):
        return f"CustomerModel('{self.organisation_name}', {self.is_active})"

