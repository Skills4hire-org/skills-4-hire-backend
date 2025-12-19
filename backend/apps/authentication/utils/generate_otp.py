import string
import random
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.authentication.otp_models import OTP_Base
import logging
from django.db import transaction
from django.db import IntegrityError
from apps.authentication.services.email_services import EmailService
from apps.authentication.services.tasks import send_email_notification 
from apps.authentication.utils.validate import _validate_subject_or_context

logger = logging.getLogger(__name__)



def generate_otp():
    max_length = getattr(settings, "MAX_OTP_LENGTH", None)

    if max_length is None:
        max_length = int(6)

    try:
        random_strings = string.ascii_uppercase + string.digits

        random_codes = "".join(random.choice(random_strings) for char in range(max_length))

        if not len(random_codes) == max_length:
            raise ValidationError("OTP misconfigured")
        
        return random_codes
    except Exception as exc:
        raise ValidationError(f"Generating OTP's Failed: {exc}")


def generate_unique_otp(max_attempts=5) -> str:
    retries = 0
    for _ in range(max_attempts):

        code = generate_otp()
        if retries >= max_attempts:
            raise ValidationError("Failed to generate otp code, maximum attmpts reached")
        
        if  not OTP_Base.objects.filter(code=code).exists():
            return code
        retries += 1
        logger.warn(f"Failed to generate OTP code: retrying {retries + 1}.....")
    
    raise ValidationError("Failed to generate after request")



def create_otp_for_user(user):
    try:
        code = generate_unique_otp()

        with transaction.atomic():
            otp_instance = OTP_Base.objects.create(user=user, code=code)

            if not otp_instance.pk:
                raise ValidationError("Error creating OTP code for user")
        logger.info("Successfully created otp for user %s", user.pk)
        return code
        
    except IntegrityError as exc:
        logger.error("Database error while creating OTP for user %s", user.id, exc_info=True)
        raise ValidationError("Database error while creating OTP.") from exc
    except ValueError as exc:
        logger.error("Invalid OTP value generated for user %s", user.id, exc_info=True)
        raise ValidationError("Error validating OTP code.") from exc

def otp_email_for_user(user, code):
    name = user.full_name
    subject, context = EmailService.send_otp_message(code, str(name))

    if not _validate_subject_or_context(subject, context):
        logger.error("Invalid email subject or context for user %s", user.id)
        raise ValidationError("Invalid email subject or context.")
        
    try:

        send_email_notification.delay(
            subject, 
            context,
            "authentication/otp.html",
            str(user.email)
        )

        logger.info("Successfully Queued ")
    except (ConnectionError, OSError) as exc:
        logger.error("Network connnectivity failed %s", exc)
        raise ValidationError("Network error, check connectivity", exc)
    except Exception as exc:
        logger.exception("Some Common Exception occurred %s", exc)
        raise ValidationError("Unknown error occurred", exc)