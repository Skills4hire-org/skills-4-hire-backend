from rest_framework.exceptions import ValidationError

from django.db import transaction

from .models import Endorsements

import logging

logger = logging.getLogger(__name__)


def endorsement_already_exists(customer_user, provider_user):
    if customer_user is None or provider_user is None:
        raise ValueError("users required")
    
    if Endorsements.objects.filter(
        endorsed_by=customer_user, provider=provider_user
        ).exists():
        return True
    return False


@transaction.atomic
def create_endorsement(**validated_data):
    if validated_data['endorsed_by'] is None or validated_data['provider'] is None:
        raise ValidationError("please provider both users")
    
    try:
        endorsement = Endorsements.objects.create(
            **validated_data
        )
        logger.info(F"Endorsement {validated_data['endorsed_by'].full_name} <-> \
                    {validated_data['provider'].profile.user.full_name}")
    except Exception as exc:
        raise ValidationError(f"Error endorsing user: {exc}")

    return endorsement


