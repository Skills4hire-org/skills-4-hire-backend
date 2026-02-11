from .provider_models import ProviderModel
from .customer_models import CustomerModel
from ..authentication.models import CustomUser

from rest_framework.exceptions import NotFound
from rest_framework.serializers import ValidationError

from django.db import transaction
from django.db.models import F
from django.db.utils import DatabaseError
from django.utils.translation import gettext_lazy as _

import logging

logger = logging.getLogger(__name__)

def get_base_profile(request):
    if hasattr(request.user, "profile"):
        base_profile = request.user.profile if request.user.profile else None
        if base_profile is None:
            raise NotFound("User base profile not found %s", request.user)
        
    return base_profile

def save_provider_profile(request):
    base_profile = get_base_profile(request)
    try:
        with transaction.atomic():
            provider_profile, created = ProviderModel.objects.get_or_create(profile=base_profile)
            if created:
                request.user.is_provider=~F("is_provider")
                request.user.save()
            logger.info("provider profile saved:  %s", request.user.email)
            return provider_profile
    except DatabaseError:
        logger.exception("Failed to save provider profile", exc_info=True)
        raise 
    except Exception:
        logger.exception("Exception occured while saving provider profile")
        raise

def save_customer_profile(request):
    base_profile = get_base_profile(request)
    try:
        with transaction.atomic():
            customer_profile = CustomerModel.objects.create(profile=base_profile)
            request.user.is_customer=~F("is_customer")
            request.user.save()
            logger.info("customer profile saved:  %s", request.user.email)
            return customer_profile
    except DatabaseError:
        logger.exception("Failed to save customer profile", exc_info=True)
        raise 
    except Exception:
        logger.exception("Exception occured while saving customer profile")
        raise

@transaction.atomic
def save_both_profiles(request):
    base_profle = get_base_profile(request)
    try:
        with transaction.atomic():
            provider_profile, created = ProviderModel.objects.get_or_create(profile=base_profle)
            if created:
                request.user.is_provider=~F("is_provider")
                request.user.save()
            customer_profile, created = CustomerModel.objects.get_or_create(profile=base_profle)
            if created:
                request.user.is_customer=~F("is_customer")
                request.user.save()
                logger.info("profile updated successfully!")
    except DatabaseError:
        logger.exception("Failed to save profiles", exc_info=True)
        raise
    except Exception:
        logger.exception("Exceptions occured while saving profiles %s", request.user.email)
        raise
    return provider_profile

def check_active_role(request):
    try:
        if not hasattr(request, "user"):
            raise ValidationError("Invalid request. Request instance is not a valid HTTP request instance")
        active_role = request.user.active_role
        logger.info("User role fetched")
        return active_role
    except Exception:
        logger.exception("Failed to fetch active role for user %s", request.user, exc_info=True)
        raise ValidationError(_("Faild to fetch the current user active role"))


            
