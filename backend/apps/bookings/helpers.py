from rest_framework.serializers import ValidationError

from ..authentication.models import CustomUser
from ..users.provider_models import ProviderModel

from django.db import transaction, DatabaseError
from django.shortcuts import get_object_or_404

from uuid import UUID
import logging

logger = logging.getLogger(__name__)

def check_request(request):
    if not hasattr(request, "user"):
        raise AttributeError("request is not a valid HTTP request instance")
    return True

def is_customer(request):
    return request.user.is_customer

def provider_profile(pk: UUID) -> ProviderModel:
    if pk is None:
        raise ValidationError("Profile pk is also required")
    try:
        with transaction.atomic():
            provider_profile = get_object_or_404(ProviderModel, pk=pk, is_active=True, is_deleted=False)
            logger.info("Base Profile fetched")
    except DatabaseError:
        logger.exception("Error fetching porvider profile")
        raise 
    except Exception as e:
        logger.exception(f"Error fetching base Profile: Error: {str(e)}")
        raise ValidationError("Failed to fetch provider profile")
    return provider_profile
