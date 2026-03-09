import requests

from django.template.loader import render_to_string
from django.conf import settings


import logging
import validators

logger = logging.getLogger(__name__)

RESEND_API_KEY = getattr(settings, "RESEND_API_KEY")
RESEND_REQUEST_PATH = getattr(settings, "RESEND_REQUEST_PATH")
APP_NAME = getattr(settings, "APP_NAME", "Skill4Hire")
FROM_EMAIL = getattr(settings, "FROM_EMAIL")


def get_headers(api_key) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    return  headers

def send_resend_email(payload):
    if payload is None:
        raise ValueError("payload for email not found")

    request_path = RESEND_REQUEST_PATH
    api_key = RESEND_API_KEY
    if api_key is None:
        raise ValueError("Resend APi Key is Empty")

    if not  validators.url(request_path):
        raise ValueError("invalid url")

    headers = get_headers(api_key)

    response = requests.post(request_path, json=payload, headers=headers)
    return response.json()


def _send_mail_base(context: dict) -> bool:
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
        payload = {
            "from": FROM_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": html_content
        }
        resend = send_resend_email(payload)
        logger.debug(resend)

    except KeyError:
        logger.exception("Missing keys in email context")
        raise 
    except Exception as e:
        logger.exception(f"Error preparing email: {str(e)}")
        raise Exception(str(e))



