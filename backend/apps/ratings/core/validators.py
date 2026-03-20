import  logging

from apps.core.utils.py import get_or_none
from apps.users.customer_models import CustomerModel
from apps.users.provider_models import ProviderModel

from apps.chats.core.utils import sanitize_message_content, validate_message_content

logger = logging.getLogger(__name__)

def validate_data(data: dict):
    """ Validates data( serializer data)
    Args:
        data (dict): Data to be validated
        expected fields: data[provider_profile_id], data[customer_profile_id]
    """

    if "provider_profile_id" in data:
        provider_profile_id = data['provider_profile_id']
    if "customer_profile_id" in data:
        customer_profile_id = data['customer_profile_id']


    if not "provider_profile_id" in data and not "customer_profile_id" in data:
        logger.debug("Both provider profile and customer profile id not provided")
        return False,  "both the provider and customer cannot the empty!"

    if "provider_profile_id" in data:
        provider_profile = get_or_none(ProviderModel, pk=provider_profile_id)
        if provider_profile is None:
            return False, "Profile not found"
    if "customer_profile_id" in data:
        customer_profile = get_or_none(CustomerModel, pk=customer_profile_id)

        if customer_profile is None:
            return False, "profile not found"
    return True, "valid"

def validate_rating(rating):
    if not isinstance(rating, int | float):
        return False, "rating can only be int or float"

    if rating < 1 or rating > 5:
        return False, "rating can only be between 1 and 5"
    return True, "valid"

def validate_reviews(review):
    if not isinstance(review, str):
        return False,  "'str' instance required"
    is_valid, message = validate_message_content(review)
    if is_valid:
        return True, "valid"
    return False, message

def privileged_to_rate_or_review(current_user, user_profile):
    if current_user == user_profile.profile.user:
        return False
    return True
