from celery import shared_task

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import F
from django.conf import settings

from rest_framework_simplejwt.tokens import OutstandingToken, BlacklistedToken

from ..one_time_password import OneTimePassword
from .email_services import _send_mail_base

import logging


User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3, retry_backoff=3)
def send_email_on_queue(self, content: dict):
    """
    Docstring for send_email_on_queue
    
    :param content: Description
    :type content: dict
    """
    try:
        _send_mail_base(context=content)
    except Exception:
        raise


@shared_task
def auto_delete_otp():
    """
    Deletes expired One-Time Password (OTP) records from the database.

    This function should be run periodically to remove OTP entries
    that are past their expiration time, helping keep the database clean.
    """

    logger.debug("Running Job: auto delete expired otps")
    try:
        expiry_minute = getattr(settings, "OTP_EXPIRY", 15) 
        with transaction.atomic():
            one_time_codes = OneTimePassword.objects.filter(
                created_at__lt=timezone.now() - timezone.timedelta(minutes=expiry_minute)
            ).update(is_active=False, is_deleted=True)
        
        logger.info(f"Automatically deleted OTP codes from the database")    
    except IntegrityError as exc:
        logger.error("Database error while auto deleting OTP",  exc_info=True)
        raise ValidationError("Database error while auto deleting OTP.") 
    except ValueError as exc:
        logger.error("Invalid error occurred", exc_info=True)
        raise ValidationError("Error auto deleting OTP code.", exc)

@shared_task    
def clean_up_expired_jwt():
    logger.debug("Running Tasks.... Clean up expired jwts refresh tokens")

    try:
        now = timezone.now()

        expired_outstainding_tokens = OutstandingToken.objects.filter(expires_at__lt=now)

        BlacklistedToken.objects.filter(token__expires_at__lt=now).delete()
        expired_outstainding_tokens.delete()

        logger.info(f"Automatically deleted Exired outstanding jwt")    
    except IntegrityError as exc:
        logger.error("Database error while auto deleting outstanding jwt",  exc_info=True)
        raise ValidationError("Database error while auto deleting JWT.") 
    except ValueError as exc:
        logger.error("Invalid error occurred", exc_info=True)
        raise ValidationError("Error auto deleting JWT token.", exc)

