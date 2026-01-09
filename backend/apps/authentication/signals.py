from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from apps.authentication.utils.generate_otp import create_otp_for_user, otp_email_for_user
from apps.users.base_model import BaseProfile

import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_save, sender=User)
def post_send_otp(sender, instance, created, **kwargs):
    
    """  
    Authomatically send user OTP after the user instance is created
    """
    if not created or not isinstance(instance, User):
        return 

    logger.debug("Start OTP generation for user %s", instance.pk)

    code = create_otp_for_user(instance)
    otp_email_for_user(instance, code)
    

@receiver(post_save, sender=User)
def post_create_profile(sender, instance, created, **kwrags):
    """ 
    Authomaticatlly creates user profiles after account registrations
    """

    if not created or not isinstance(instance, User):
        return 
    
    if BaseProfile.objects.filter(user=instance).exists():
        return 

    profile = BaseProfile(user=instance, display_name=instance.full_name)

    profile.save()

    