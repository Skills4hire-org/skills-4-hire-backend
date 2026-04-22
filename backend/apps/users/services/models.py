
import uuid
from django.db import models
from django.core.exceptions import ValidationError

from ..provider_models import ProviderModel


class ServiceCategory(models.Model):

    service_category_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, 
        editable=False, unique=True, db_index=True
    )

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.name:
            self.name = self.name.strip().title()
        super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
class Service(models.Model):
    service_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL, null=True, related_name="services"
    )
    profile = models.ForeignKey(
        ProviderModel,
        related_name="services",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    min_charge = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    max_charge = models.DecimalField(max_digits=12, decimal_places=2, null=True)

    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["profile", "is_active"]),
            models.Index(fields=["deleted_at"]),
            models.Index(fields=['is_active'])
        ]

    def clean(self):
        if self.min_charge is not None and self.max_charge is not None:
            if self.min_charge > self.max_charge:
                raise ValidationError(
                    {"min_charge": "min_charge must be less than or equal to max_charge."}
                )

    def __str__(self):
        return f"{self.name} ({self.service_id})"


class ServiceAttachment(models.Model):
    image_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )
    service = models.ForeignKey(
        Service,
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    image_url = models.URLField(max_length=2048)
    image_public_id = models.CharField(max_length=512)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["service", "is_active"]),
        ]

    def __str__(self):
        return f"Attachment {self.image_id} for service {self.service.pk}"