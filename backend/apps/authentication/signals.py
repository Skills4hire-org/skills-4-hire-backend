from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

from ..users.base_model import BaseProfile
from ..wallet.services import WalletService
from .utils.helpers import (create_otp_for_user)
from .helpers import _send_email_to_user, logger
from .utils.template_helpers import genrate_context_for_otp
from ..referral.services.utils import generate_code
from ..referral.services.referral_services import ReferralService

import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=User)
def post_save_otp_after_account_registration(sender, instance, created, **kwargs):
    """ Automatically create and send OTP and verification URL to user after account registration """
    if not isinstance(instance, User):
        return 
    if not created: 
        return

    logger.info(f"Signal fired for user: {instance.email}")
    try:
        code = create_otp_for_user(instance)
        context = genrate_context_for_otp(code=code, email=instance.email, full_name=instance.full_name)
        _send_email_to_user(context)
        logger.debug(f"OTP created and email sent for user: {instance.email}")
    except Exception as e:
        logger.error(f"Error in post_save signal for {instance.email}: {e}")


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

@receiver(post_save, sender=User)
def auto_create_wallet(sender, instance, created, **kwargs):
    if not created or not isinstance(instance, User):
        return 
    if WalletService.create_wallet(instance):
        logger.info("Wallet created successfully")
    return 

@receiver(post_save, sender=User)
def create_referral_code(sender, instance, created, **kwargs):
    logger.info("Starting Task to referral code creation")
    if not created:
        return 
    
    code = generate_code(instance)
    logger.info(f"code generated: {code[:3]}...")
    try:
        # create referral code this user
        service = ReferralService()
        create = service.create_referral_code(instance, code)
        if create['status']:
            logger.info("referral code created")
    except Exception as exc:
        logger.error(str(exc))
        return 
    

