from rest_framework.serializers import ValidationError

from ..authentication.models import CustomUser
from ..users.base_model import BaseProfile

from django.db import transaction, DatabaseError
from django.shortcuts import get_object_or_404

from uuid import UUID

def check_request(request):
    if not hasattr(request, "user"):
        raise AttributeError("request is not a valid HTTP request instance")
    return True
    
def check_user_wallet(request):
    if check_request(request):
        if hasattr(request.user, "wallet"):
            return request.user.wallet
    return False

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
            base_profile = get_object_or_404(BaseProfile, pk=pk, active=True, is_deleted=False)
    except DatabaseError:
        raise 
    except Exception:
        raise
    return base_profile