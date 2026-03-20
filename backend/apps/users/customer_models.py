from django.db import models
from django_countries.fields import CountryField
from django.utils.text import gettext_lazy as _
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

    profile = models.OneToOneField(
        BaseProfile, on_delete=models.CASCADE,
        related_name="customer_profile", db_index=True)

    website = models.URLField(blank=True, null=True)

    city = models.CharField(blank=True, null=True)
    country = CountryField(blank=True, null=True)

    industry_name = models.CharField(blank=True, null=True, db_index=True)

    total_hires  = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _("Customer Profile")
        verbose_name_plural = _("Customer Profiles")
        # ordering = ["-created_at"]
        indexes = [
            models.Index(fields=("is_active",), name="dele_acti_idx"),
            models.Index(fields=("is_active", "is_verified"), name="very_dele_acti_idx")
        ]

    def get_country(self):
        if self.country:
            return str(self.country)

    def __str__(self):
        return f"CustomerModel('{self.profile.user.full_name}', {self.is_active})"


    def clean(self):
        if self.industry_name:
            self.industry_name.title()

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.profile.user.is_verified:
            self.is_verified = True
        super().save(*args, **kwargs)
