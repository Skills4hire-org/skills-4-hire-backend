from rest_framework.serializers import ValidationError

from ..authentication.models import CustomUser
from ..users.base_model import BaseProfile

from django.db import transaction, DatabaseError
from django.shortcuts import get_object_or_404

from uuid import UUID
import logging

logger = logging.getLogger(__name__)

def check_request(request):
    if not hasattr(request, "user"):
        raise AttributeError("request is not a valid HTTP request instance")
    return True
    
def get_user_wallet(request=None, user=None):
    if user is None and request is not None:
        if check_request(request):
            user = getattr(request, "user")
    if user and hasattr(user, "wallet"):
        return user.wallet
    return None

def is_customer(request):
    if check_request(request):
        role = getattr(request.user, "active_role", None)   
        if role is None:
            raise ValidationError("Role is not set for user, Complete onboarding to continue")
        if role == CustomUser.RoleChoices.CUSTOMER:
            return True
    return False

def _base_profile_by_pk(pk: UUID) -> BaseProfile:
    if pk is None:
        raise ValidationError("Profile pk is also required")
    if not isinstance(pk, UUID):
        raise ValidationError("PK is not a valid UUID instance")
    try:
        with transaction.atomic():
            base_profile = get_object_or_404(BaseProfile, pk=pk, is_active=True, is_deleted=False)
            logger.info("Base Profile fetched")
    except DatabaseError:
        logger.exception("Error fetching Base profile")
        raise 
    except Exception as e:
        logger.exception(f"Error fetching base Profile: Error: {str(e)}")
        raise ValidationError("Failed to fetch base profile")
    return base_profile