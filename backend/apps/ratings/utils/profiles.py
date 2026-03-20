from ..models import ProfileReview, ProfileRating

import logging
import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import serializers

logger = logging.getLogger(__name__)


def get_profile_by_id(profile_id: uuid) -> dict:
    if profile_id is None:
        logger.error("PROFILE_ID_EMPTY")
        return {"status": "Failed", "detail": "profile Id is None"}

    # if not isinstance(profile_id, uuid):
    #     logger.error("PROFILE_ID_INVALID")
    #     return {"status": "Failed",, "detail": "profile Id is invalid. Not a valid UUID"}
    # try:
    #     with transaction.atomic():
    #         profile = get_object_or_404(BaseProfile, pk=profile_id.strip())

    # except Exception:
    #     logger.exception("CANT_FETCH_PROFILE_DATA")
       
    # return profile

def get_user_with_profile(self):
    request = self.context.get("request")
    if request.user is None:
        raise serializers.ValidationError("Authentication required to create a rating.") 
    profile_obj = self.context.get("profile")
    if profile_obj == getattr(request.user, "profile", None):
        raise serializers.ValidationError("You cannot review your own profile.")
    
    return request, profile_obj

def customer_email_or_provider_email_or_none(obj, action):
    """ obj: either ProfileRating instance or ProfileReview Instance
        action:
            required_fields: provider or customer
            which user email to fetch: can be the customer or provider
    """

    valid_objs  = (ProfileRating, ProfileReview)
    if not isinstance(obj, valid_objs):
        return False, None
    if action.lower() == "provider":
        provider_profile = obj.provider_profile
        if provider_profile is None:
            return False, None
        return True, provider_profile.profile.user.email

    elif action.lower() == "customer":
        customer_profile = obj.customer_profile
        if customer_profile is None:
            return False, None
        return True, customer_profile.profile.user.email

    else:
        return False, None

