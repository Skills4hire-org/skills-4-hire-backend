from apps.authentication.services.tasks import send_email_notification
from apps.authentication.utils.validate import _validate_subject_or_context
import logging

logger  = logging.getLogger(__name__)
def send_email_to_user(subject, context, template_name, receipient):


    if not _validate_subject_or_context(subject, context):
        logger.error("Invalid email subject or context for user %s", receipient)
        raise ValidationError("Invalid email subject or context.")
        
    try:

        send_email_notification.delay(
            subject, 
            context,
            template_name,
            receipient
        )

        logger.info("Successfully Queued ")
    except (ConnectionError, OSError) as exc:
        logger.error("Network connnectivity failed %s", exc)
        raise ValidationError("Network error, check connectivity", exc)
    except Exception as exc:
        logger.exception("Some Common Exception occurred %s", exc)
        raise ValidationError("Unknown error occurred ")

