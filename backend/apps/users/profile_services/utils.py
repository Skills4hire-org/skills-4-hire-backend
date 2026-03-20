from ..customer_models import CustomerModel
from ..profile_avater.models import Avatar
from ...core.utils.py import get_or_none

from ..provider_models import ProviderModel

from django.contrib.auth import  get_user_model

UserModel = get_user_model()

def already_has_a_profile(user) -> bool:
    if not isinstance(user, UserModel):
        raise ValueError("not a valid user model")
    provider_profile = get_or_none(ProviderModel, profile=user.profile)
    customer_profile = get_or_none(CustomerModel, profile=user.profile)
    if provider_profile is None and customer_profile is None:
        return False

    return True

def get_profile_avatar(profile):

    base_profile = profile.profile
    try:
        avatar = base_profile.avatar
    except Avatar.DoesNotExist:
        return None
    return avatar


