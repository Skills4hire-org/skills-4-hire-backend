from rest_framework.exceptions import ValidationError

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

from ..exceptions import  retry_on_failure
from ..one_time_password import OneTimePassword

import hashlib
import logging
import string
import random

max_retries = getattr(settings, "MAX_RETRY", 4)
BASE_URL = getattr(settings, "BASE_URL", None)
logger = logging.getLogger(__name__)
User = get_user_model()

def _hash_otp_code(code: str):
    if code is None:
        raise ValidationError("Code cannot be empty")
    hash_code = hashlib.sha256(code.encode()).hexdigest()
    return hash_code

def _generate_code():
    try:
        max_code = getattr(settings, "MAX_CODE", None)
        if max_code is None:
            max_code = int(6)
        generate_from = string.digits
        new_code = "".join(random.choice(generate_from) for _ in range(max_code))
        return new_code
    except Exception:
        logger.exception("Exception while generating otp code", exc_info=True)
        raise Exception()

@retry_on_failure(max_retries)
def _generate_unique_otp():
    code = _generate_code()
    hash_code = _hash_otp_code(code)
    if OneTimePassword.objects.filter(hash_code=hash_code).exists():
        logger.warning(_("OTP Already Exists!"))
        raise ValidationError(_("Failed. OTP already exists"))
    return code, hash_code

def create_otp_for_user(user):
    if not isinstance(user, User):
        raise ValidationError(_("%s is not a valid 'User' Instance", user))
    code, hash_code = _generate_unique_otp()
    try:
        with transaction.atomic():
            OneTimePassword.objects.create(user=user, hash_code=hash_code) 
        logger.debug("successfully created and saved OTP for user %s", user)
    except IntegrityError as exc:
        logger.error("Database error while creating OTP for user %s", user.id, exc_info=True)
        raise ValidationError("Database error while creating OTP.") from exc
    except ValueError as exc:
        logger.error("Invalid OTP value generated for user %s", user.id, exc_info=True)
        raise ValidationError("Error validating OTP code.") from exc
    return code