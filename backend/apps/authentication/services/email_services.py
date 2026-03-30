import requests

from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail


import logging
import validators

logger = logging.getLogger(__name__)

APP_NAME = getattr(settings, "APP_NAME", "Skill4Hire")


def send_mail_base(context: dict) :
    """
    Docstring for _send_mail_base
    
    :param context: Description
    :type context: dict
    :return: Description
    :rtype: bool
    """
    context.update({"app_name": APP_NAME})
    logger.debug(context)
    try:
        html_content = render_to_string(context.get("template_name"), context)
        subject = context.get("subject")
        to_email = context.get("to_email")
        
        send_mail(
            subject=subject,
            from_email="noreply@skills4hireapp.com",
            recipient_list=[to_email],
            fail_silently=False,
            message='',
            html_message=html_content,
        )
    except KeyError:
        logger.exception("Missing keys in email context")
        raise 
    except Exception as e:
        logger.exception(f"Error preparing email: {str(e)}")
        raise Exception(str(e))

