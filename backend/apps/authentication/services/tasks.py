from celery import shared_task
from apps.authentication.services.email_services import Email, EmailService
from django.core.exceptions import ValidationError
import logging
from apps.authentication.otp_models import OTP_Base
from django.db import IntegrityError, transaction

logger = logging.getLogger(__name__)

@shared_task
def send_email_notification(subject, context, template_name, receipient):
    """
    Sends a notification email asynchronously using Celery.

    Args:
        subject (str): Email subject.
        context (dict): Template rendering context.
        template_name (str): Path to the email template.
        receipient (str): Recipient email address.
    """
    try:
        # Create and send Notification email
        service = EmailService(
            email=Email(
                subject=subject,
                context=context,
                template_name=template_name,
                receipient=receipient
            )
        )

        service.send_mail()
        logger.info(f"Notification Email sent Successfully:", receipient)

    except ValidationError:
        raise
    except (ConnectionError, TimeoutError) as net_err:
        logger.error("Network error while sending email: %s", net_err, exc_info=True)
        raise ValidationError(f"Network error while sending email: {net_err}") from net_err
    except Exception as exc:
        logger.exception("Unexpected error while sending email.")
        raise ValidationError(f"Unexpected error while sending email: {exc}") from exc


@shared_task
def auto_delete_otp():
    """
    Deletes expired One-Time Password (OTP) records from the database.

    This function should be run periodically to remove OTP entries
    that are past their expiration time, helping keep the database clean.
    """

    logger.debug("Running Job: auto delete expired otps")

    deleted_otps = 0
    try:
        otp_records = OTP_Base.objects.all().only("otp_id", "code")

        for otp in otp_records:
            with transaction.atomic():
                if otp.is_expired():
                    deleted_otps += 1
                    otp.delete()
        logger.info(f"Automatically deleted {deleted_otps} OTP codes from the database")    
    except IntegrityError as exc:
        logger.error("Database error while auto deleting OTP",  exc_info=True)
        raise ValidationError("Database error while auto deleting OTP.") 
    except ValueError as exc:
        logger.error("Invalid error occurred", exc_info=True)
        raise ValidationError("Error auto deleting OTP code.", exc)
        