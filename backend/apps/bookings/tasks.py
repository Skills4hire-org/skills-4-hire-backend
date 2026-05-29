from celery import shared_task

from django.contrib.auth import get_user_model
from ..posts.services.trust_score_service import compute_trust_score

UserModel = get_user_model()
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def auto_update_trust_score(self):
    """
    Task to auto update trust score for all providers with latest platform engagements
    """
    try:
        providers = UserModel.objects.filter(is_provider=True)

        for user in providers:
            compute_trust_score(user=user)
    except Exception as e:
        logger.error(str(e))
        self.retry(exc=e, countdown=60 * 3)


