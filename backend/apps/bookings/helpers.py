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
    if check_request(request):
        role = getattr(request.user, "active_role", None)   
        if role is None:
            raise ValidationError("Role is not set for user, Complete onboarding to continue")
        if role == CustomUser.RoleChoices.CUSTOMER:
            return True
    return False

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

def user_in_booking(user, booking) -> bool:
    return user in (
        booking.customer,
        booking.provider.profile.user
    )

def can_delete_booking(user, booking):
    return (
        booking.is_active == True
        and booking.is_deleted == False
        and booking.customer == user
    )