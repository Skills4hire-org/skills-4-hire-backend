from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

from .models import Message, Negotiations
from .services.support_service import add_staff_to_all_support_rooms
from apps.core.utils.py import log_action


import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(signal=post_save, sender=User)
def add_staff_to_support_rooms(sender, instance, created, **kwargs):
    """
    When a staff user is created, ensure they have access to all support rooms.
    """
    if not created or not getattr(instance, 'is_staff', False):
        return

    try:
        add_staff_to_all_support_rooms(instance)
    except Exception:
        logger.exception("Failed to add new staff user to support rooms.")




