from django.db import models
from django.contrib.auth import get_user_model

from ...users.provider_models import ProviderModel

import uuid

UserModel = get_user_model()

class Endorsements(models.Model):

    endorsement_id = models.UUIDField(
        primary_key=True, editable=False,
        unique=True, default=uuid.uuid4,
    )

    endorsed_by = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='endorsed_by')
    provider = models.ForeignKey(ProviderModel, on_delete=models.CASCADE, related_name="receiver_endorse")


    reason = models.TextField(max_length=500, null=False, blank=False)
    extra_message = models.CharField(max_length=255, null=True, blank=True)

    is_hidden = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    endorsed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Endorsement {self.endorsement_id}"
    
    class Meta:
        constraints  = [
            models.UniqueConstraint(
                fields=("endorsed_by", 'provider'), name='unique_sender'
            )
        ]
        indexes = [
            models.Index(
                fields=('endorsement_id',)
            ),
            models.Index(
                fields=("endorsed_at",)
            ),
            models.Index(
                fields=("updated_at",)
            ),
            models.Index(
                fields=("reason",)
            )
        ]

        verbose_name = 'Endorsement'


