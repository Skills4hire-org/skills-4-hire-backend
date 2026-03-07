import uuid

from .services.tasks import send_email_on_quene
from .utils.helpers import verify_hashed_code
from .one_time_password import OneTimePassword

from rest_framework_simplejwt.tokens import OutstandingToken, BlacklistedToken
from rest_framework.exceptions import ValidationError, NotFound

from django.contrib.auth import get_user_model
from django.db import transaction

import logging
import email_validator

logger  = logging.getLogger(__name__)
User = get_user_model()

def _send_email_to_user(context: dict):
    """
    Docstring for _send_email_to_user
    
    :param subject: Description
    :type subject: str
    :param template_name: Description
    :type template_name: str
    :param content: Description
    :type content: dict
    :param user: Description
    """
    if context is None:
        raise ValidationError("Missing Content Body")
    email = context.get("email")
    subject = context.get("subject")
    template_name = context.get("template_name")
    if not email:
        raise ValidationError("email cannot be empty")
    if not subject:
        raise ValidationError("Email requires a subject")
    if not template_name:
        raise ValidationError("Please provide a template name to send well structured notifications")
    
    if not User.objects.filter(email=email).exists():
        raise ValidationError("User dosent exits in our database")
    email = email
    context.update({"to_email": email, "subject": subject, "template_name": template_name})
    try:
        send_email_on_quene.delay(context)
        logger.info(f"Email message quened for {email}")
        return {"success": True, "message": "Email sent to quene successfully"}
    except Exception as e:
        logger.exception("Exception while sending email.", exc_info=True)
        raise


def blacklist_outstanding_token(user):
    if user is None:
        raise ValidationError("User instance is required")

    try:
        outstanding_tokens = OutstandingToken.objects.filter(user=user)

        if outstanding_tokens is None:
            logger.info("No Outstanding token found for %s",  user)

        BlacklistedToken.objects.bulk_create([
            BlacklistedToken(token=token) for token in outstanding_tokens
            ], ignore_conflicts=True)
        logger.debug(f"Blacklist {outstanding_tokens.count()} token")

    except Exception as exc:
        raise ValidationError(F"Error blacklisting tokens: {exc}")

def validate_email(email):
    try:
        valid_email = email_validator.validate_email(email, check_deliverability=True)
    except email_validator.EmailNotValidError as exc:
        raise ValidationError("Invalid email address provided")
    return valid_email.normalized

def _get_user_by_email(email: str):
    try:
        user = User.objects.get(email__iexact=email, is_deleted=False, is_active=True)
        return user
    except User.DoesNotExist:
        return None

def get_user_by_pk(pk: uuid.UUID):
    try:
        user = User.objects.get(user_id=pk, is_deleted=False, is_active=True)
        return user
    except User.DoesNotExist:
        return NotFound("User not found", code=404)

def _get_code_intance_or_none(code: str, user = None) -> OneTimePassword:
    try:
        if user:
            code_instance = OneTimePassword.objects.get(raw_code=code, user=user, is_active=True, is_used=False)
        else:
            code_instance = OneTimePassword.objects.get(raw=code, is_active=True, is_used=False)
        code_instance_valid = verify_hashed_code(code, code_instance.hash_code)
        if code_instance_valid:
            return code_instance
        return None
    except OneTimePassword.DoesNotExist:
        return None
    
def verify_account(user, code_instance: OneTimePassword) -> bool:
    is_verified = bool
    if not user:
        raise ValidationError("Custom user instane cannot be None on account Verification")
    with transaction.atomic():
        user.is_active = True
        user.is_verified = True
        try:
            user.save()
            is_verified = True
        except Exception:
            is_verified = False
    if code_instance:
        try:
            with transaction.atomic():
                code_instance.is_used = True
                code_instance.is_active = False
                code_instance.save()
        except Exception:
            raise Exception("Error updating code instance")
    
    return is_verified