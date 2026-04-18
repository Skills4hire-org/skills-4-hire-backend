from rest_framework.exceptions import ValidationError

from django.db.models import Q

from ..models import ProfileReview

import logging
logger = logging.getLogger(__name__)

class ReviewService:

    def _dublicate_reviews(self, user, provider) -> bool:
        if ProfileReview.objects.filter(
            Q(reviewed_by=user, provider_profile=provider) |
            Q(provider_profile__profile__user=user, reviewed_by__profile__provider_profile=provider),
            is_active=True
        ).exists():
            
            return True
        return False

    def _cant_review_yourself(self, user, provider):
        if user == provider.profile.user:
            return True
        return False
            

    def create_review(self, validated_data):

        try:
            review_instance = ProfileReview.objects.create(
                **validated_data
            )
            return review_instance
        
        except Exception as e:
            logger.error(e)
            raise ValidationError(f"error creating review {e}")


