from rest_framework.exceptions import ValidationError

from .ratings import RatingService
from ..models import ProfileReview

class ReviewService:


    def __init__(self, review, reviewed_by):
        self.review = review
        self.reviewed_by = reviewed_by

    def create_review(self, user_profile, validated_data):
        customer_pofile, provider_profile = RatingService()._validate_user_profile(user_profile)

        if customer_pofile is None and provider_profile is None:
            raise ValueError("no_profile_found")
        validated_data.pop("review")
        try:
            instance = ProfileReview(review=self.review, reviewed_by=self.reviewed_by, **validated_data)

            if customer_pofile:
                instance.customer_profile = customer_pofile
            elif provider_profile:
                instance.provider_profile = provider_profile
            else:
                instance.save()
            instance.save()
        except Exception as e:
            raise ValidationError(f"error creating review {e}")
        return instance


