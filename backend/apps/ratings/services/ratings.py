from anyio import create_udp_socket
from django.db import transaction

from apps.users.customer_models import CustomerModel
from apps.users.provider_models import ProviderModel
from rest_framework.exceptions import ValidationError

from apps.ratings.models import ProfileRating, UserModel
from typing import  Optional

class RatingService:

    def __init__(self, rating: Optional[int] = None, rate_by: Optional[UserModel] = None):
        self.rating = rating
        self.rate_by = rate_by

    @staticmethod
    def _validate_user_profile(user_profile):
        customer_profile = None
        provider_profile = None


        if isinstance(user_profile, CustomerModel):
            customer_profile = user_profile
        elif isinstance(user_profile, ProviderModel):
            provider_profile = user_profile
        else:
            raise ValueError("Profile is not a valid profile instance")

        return customer_profile, provider_profile

    @transaction.atomic
    def create_rating(self, validated_data: dict, user_profile):
        customer_profile, provider_pofile = self._validate_user_profile(user_profile)

        if customer_profile is None and provider_pofile is None:
            raise ValueError("no profile is provided")

        validated_data.pop("rating")
        try:
            instance = ProfileRating(
                rating=self.rating, rate_by=self.rate_by,
                **validated_data
            )
            if customer_profile:
                instance.customer_profile = customer_profile
            elif provider_pofile:
                instance.provider_profile = provider_pofile
            else:
                instance.save()
            instance.save()
        except Exception as e:
            raise ValidationError(f"error creating rating: {e}")
        return instance



