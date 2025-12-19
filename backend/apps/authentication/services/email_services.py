from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from typing import Optional
import logging
from django.utils.html import strip_tags
from django.core.exceptions import ValidationError
from dataclasses import dataclass
from django.utils import timezone

logging.basicConfig(level=logging.INFO)

email_host = getattr(settings, "EMAIL_HOST_USER")
app_name = getattr(settings, "APP_NAME")
@dataclass
class Email:
    """
    A Dataclass for handling email data 
    """
    subject: str
    context: dict
    template_name: str
    host_user: Optional[str] = email_host
    receipient: Optional[str] = None 



class EmailService:
    def __init__(self, email: Email):
        self.subject = email.subject
        self.context = email.context
        self.template_name = email.template_name
        self.host_user = email.host_user
        self.receipient = email.receipient


    def _validate_subject(self):
        """ for mat self.subject properly and mark unknow if not provided"""
        if not self.subject or not str(self.subject).strip():
            self.subject = "Unknown"
        else:
            self.subject = str(self.subject).strip()

    def send_mail(self):
        if not self._validate_subject():
            logging.info("Error occurred while checking for message")
            
        if not self.receipient:
            logging.info("Receipient list cannot be empty")
            raise ValueError("Receipient list cannot be empty")

        if not self.template_name or not self.context:
            logging.warn("template name and context are not provided")
            raise ValueError("template name and context are not provided")

        html_content = render_to_string(self.template_name, self.context)

        html_text = strip_tags(html_content) # returns a text vesiosn of the html page

        try:
            message = EmailMultiAlternatives(
                subject=self.subject,
                body=html_text,
                from_email=self.host_user,
                to=[self.receipient]
            )

            if html_content:
                message.attach_alternative(html_content, "text/html")
            message.send(fail_silently=False)
        except Exception as exc:
            logging.error(f"error occurred: {exc}")
            raise ValidationError(f"Sending  Email failed: {exc}")

    @staticmethod
    def send_otp_message(code, name):
        subject = f"{app_name} Verification code"
        context = {
            "code": code,
            "name": str(name),
            "app_name": app_name,
            "year": timezone.now().year

        }
        return subject,  context

    def pasword_reset_message(**kwargs):
        name = kwargs.get("name", None)
        code = kwargs.get("code", None)
        subject = f"{app_name} Password Reset code"
        context = {
            "code": code,
            "name": str(name),
            "app_name": app_name,
            "year": timezone.now().year

        }
        return subject,  context

        