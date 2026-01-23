from celery import shared_task
from django.contrib.auth import get_user_model
from ..authentication.models import CustomUser
from django.core.exceptions import ValidationError
import logging
from django.db import IntegrityError

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def auto_update_role():
    """" Authomaticatically update user role depending on the active role for users"""

    logger.debug("Running Tasks... Updating role")
    try:
        User.objects.filter(active_role=CustomUser.RoleChoices.CLIENT).update(is_client=True)

        User.objects.filter(active_role=CustomUser.RoleChoices.SERVICE_PROVIDER).update(is_provider=True)
        logger.info(f"Automatically updated user roles")    
    except IntegrityError as exc:
        logger.error("Database error while auto updating roles",  exc_info=True)
        raise ValidationError("Database error while auto updating user roles.") 
    except ValueError as exc:
        logger.error("Invalid error occurred", exc_info=True)
        raise ValidationError("Error auto updating user roles.", exc)


