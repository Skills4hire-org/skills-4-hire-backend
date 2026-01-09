from django.db import models
import uuid
from .base_model import BaseProfile

class ClientModel(models.Model):

    client_id = models.UUIDField(
        max_length=20, 
        primary_key=True,
        default=uuid.uuid4,
        unique=True, 
        db_index=True
    )

    profile = models.OneToOneField(BaseProfile, on_delete=models.CASCADE, related_name="client_profile")

    organisation_name = models.CharField(max_length=200, blank=True)
    organisation_type = models.CharField(max_length=200, blank=True)

    industry = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    total_hires  = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"ClientModel('{self.organisation_name}', {self.is_active})"

