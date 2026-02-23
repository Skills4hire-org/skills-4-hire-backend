from ..models import ProfileReview

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