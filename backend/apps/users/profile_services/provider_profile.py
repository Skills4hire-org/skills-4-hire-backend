from django.db import transaction

from ..base_model import BaseProfile
from ..provider_models import ProviderModel



class ProviderProfileServices:

    @transaction.atomic
    def create_provider_profile(self, user_base_profile, validate_data: dict | None = None):
        if not isinstance(user_base_profile, BaseProfile):
            raise ValueError("this is not a valid base profile")

        try:
            if validate_data is not None:
                provider_profile = ProviderModel.objects.get_or_create(profile=user_base_profile, **validate_data)
            else:
                provider_profile = ProviderModel.objects.get_or_create(profile=user_base_profile, professional_title="new")
            setattr(user_base_profile.user, "is_provider", True)
            user_base_profile.user.save(update_fields=["is_provider"])
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Failed to create provider profile for base profile %s: %s", getattr(user_base_profile, 'id', None), e)
            raise ValueError("Failed to create provider profile")
        return provider_profile
