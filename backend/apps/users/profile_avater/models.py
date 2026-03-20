import validators
from django.db import models
from django.utils.text import gettext_lazy as _

from ..base_model import BaseProfile

import uuid


class Avatar(models.Model):
    avatar_id = models.UUIDField(
        primary_key=True, unique=True, null=False,
        default=uuid.uuid4, max_length=20
    )

    profile = models.OneToOneField(BaseProfile, on_delete=models.CASCADE, related_name="avatar")

    description = models.TextField(blank=True, null=True)
    avatar = models.URLField(blank=True, null=True, max_length=200)

    avatar_public_id = models.CharField(max_length=200, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = _("Profile Avatars")
        verbose_name = _("Profile Avatar")
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['avatar']),
            models.Index(fields=['is_active'])
        ]

    def clean(self):
        if not validators.url(self.avatar):
            raise ValueError("profile avatar is invalid")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ProfileAvatar: {self.profile.display_name}, {self.is_active}"

