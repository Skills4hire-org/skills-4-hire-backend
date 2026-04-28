# from celery import shared_task
# from django.contrib.auth import get_user_model
# from ..authentication.models import CustomUser
# from django.core.exceptions import ValidationError
# import logging
# from django.db import IntegrityError

# logger = logging.getLogger(__name__)
# User = get_user_model()


# @shared_task(bind=True, max_retries=3)
# def auto_update_role(self):
#     """" Authomaticatically update user role depending on the active role for users"""

#     logger.debug("Running Tasks... Updating role")
#     try:
#         User.objects.filter(active_role=CustomUser.RoleChoices.CUSTOMER).update(is_customer=True)

#         User.objects.filter(active_role=CustomUser.RoleChoices.SERVICE_PROVIDER).update(is_provider=True)
#         logger.info(f"Automatically updated user roles")    
#    except 


