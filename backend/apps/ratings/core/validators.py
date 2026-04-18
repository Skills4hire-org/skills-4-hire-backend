import  logging

from apps.chats.core.utils import validate_message_content

logger = logging.getLogger(__name__)

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
