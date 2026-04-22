from django.db import models
from django.conf import settings

from ..provider_models import ProviderModel

import uuid

UserModel = settings.AUTH_USER_MODEL

class Favourite(models.Model):

    favourite_id = models.UUIDField(
        primary_key=True, editable=False, unique=True,
        default=uuid.uuid4, db_index=True
    )

    owner = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name="favourite_owner")

    providers = models.ManyToManyField(ProviderModel, related_name="favouites", db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        verbose_name = 'Favourite'
        verbose_name_plural = "Favourites"

