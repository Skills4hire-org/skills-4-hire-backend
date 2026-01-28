from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Content

from django.template.loader import render_to_string
from django.conf import settings

from rest_framework.exceptions import ValidationError

import logging
import os

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = getattr(settings, "SENDGRID_API_KEY", None)
SENDGRID_SENDER = getattr(settings, "SENDGRID_SENDER", None)
APP_NAME = getattr(settings, "APP_NAME", "SkillSpeed")

def _send_mail_base(context: dict) -> bool:
    """
    Docstring for _send_mail_base
    
    :param context: Description
    :type context: dict
    :return: Description
    :rtype: bool
    """
    if SENDGRID_API_KEY is None:
        logger.warning("SENDGRID_API_KEY is empty")
        raise ValidationError("'SENDGRID_API_KEY' cannot be empty")
    if SENDGRID_SENDER is None:
        logger.warning("'SENDGRID_SENDER' sender is empty, authenticate in sendgrid dashboard")
    if any(value is None for value in context.values()):
        logger.warning("Email context is incomplete")
        raise ValidationError("Email context cannot have None values")
    context.update({"app_name": APP_NAME})
    print(context)
    try:
        html_content = render_to_string(context.get("template_name"), context)
        client = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        message = Mail(
            from_email=From(email=SENDGRID_SENDER),
            to_emails=To(email=context.get("to_email")),
            subject=context.get("subject"),
            html_content=Content("text/html", html_content)
        )
        
        response = client.send(message=message)
        if response.status_code != 202:
            logger.error(f"SendGrid failed: {response.body}")
            raise ValidationError(f"Email failed with status: {response.status_code}")
    except KeyError:
        logger.exception("Missing keys in email context")
        raise 
    except Exception as e:
        logger.exception("Error preparing email")
        raise



