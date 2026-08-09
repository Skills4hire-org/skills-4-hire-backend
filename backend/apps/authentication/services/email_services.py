from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

import logging

logger = logging.getLogger(__name__)

APP_NAME = getattr(settings, "APP_NAME", "Skill4Hire")


def send_mail_base(context: dict, from_email: str = settings.DEFAULT_FROM_EMAIL) :
    """
    Docstring for send_mail_base
    
    :param context: Description
    :type context: dict
    :return: Description
    :rtype: bool
    """
    context.update({"app_name": APP_NAME, "year": str(timezone.now().year)})
    try:
        html_content = render_to_string(context.get("template_name"), context)
        subject = context.get("subject")
        to_email = context.get("to_email")
        
        send_mail(
            subject=subject,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
            message="",
            html_message=html_content,
        )
    except KeyError:
        logger.error("Missing keys in email context")
        raise 
    except Exception as e:
        logger.error("Error preparing email: %s", e)
        raise Exception("Error preparing email")

