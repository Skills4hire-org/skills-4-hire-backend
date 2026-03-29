from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings

from .models import Endorsements
from ...authentication.helpers import _send_email_to_user
from .helpers import generate_context_for_endorsement_email

import logging


logger = logging.getLogger(__name__)

@receiver(signal=post_save, sender=Endorsements)
def send_provider_endorsement_message(sender, instance, created, **kwargs):
    if not instance:
        return
    
    if not created:
        return
    
    app_name = getattr(settings, "APP_NAME", "Skills4Hire")
    endorsement_url = settings.BASE_URL + f"api/v1/endorsement-detail/{instance.pk}/"
    frontend_url = getattr(settings, "FRONTEND_URL", 'http://localhost/')

    sender_full_name = instance.endorsed_by.full_name

    receiver_full_name= instance.provider.profile.user.full_name
    email = instance.provider.profile.user.email

    # send real time email to provider
    context  = generate_context_for_endorsement_email(
        email=email, endorsement_url=endorsement_url,
        full_name=receiver_full_name, frontend_url=frontend_url,
        template_name='chats/endorse.html', APP_name=app_name,
        sender_full_name=sender_full_name
    )
    try:
        _send_email_to_user(context)
    except Exception as exc:
        logger.exception(f"Error: {str(exc)}")
    



