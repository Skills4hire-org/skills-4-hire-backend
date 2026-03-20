from django.db import  models
from django.contrib.auth import  get_user_model

from ..base_model import BaseProfile

from postal_regex.validator import validate as _validate_postal_code

import uuid
import logging

logger = logging.getLogger(__name__)
UserModel = get_user_model()


class UserAddress(models.Model):
    """Detailed address for users."""
    address_id = models.UUIDField(
        max_length=20, primary_key=True,
        unique=True, db_index=True,
        default=uuid.uuid4
    )

    user_profile = models.ForeignKey(BaseProfile, on_delete=models.CASCADE, related_name="addresses")

    street_address = models.CharField(max_length=255)
    apartment = models.CharField(max_length=100, blank=True)

    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "User Addresses"
        constraints = [
            models.UniqueConstraint(fields=['postal_code', "user_profile"], name='unique_postal_code')
        ]
    def __str__(self):
        return f"UserAddress: {self.user_profile.user.full_name} - {self.postal_code}"

    @staticmethod
    def validate_postal_code(code) -> bool:
        postal_code = code.strip()
        is_valid = _validate_postal_code("NG", postal_code)
        if not is_valid:
            return False
        return True

    def clean(self):
        if not UserAddress().validate_postal_code(self.postal_code):
            logger.debug("Postal code not valid")
            raise ValueError("postal code is invalid")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

