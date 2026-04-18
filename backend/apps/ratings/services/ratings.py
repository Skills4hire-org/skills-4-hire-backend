from django.db.models import Q
from apps.ratings.models import ProfileRating


class RatingService:

    def _duplicate_rating(self, user, provider):

        if ProfileRating.objects.filter(
            Q(rate_by=user, provider_profile=provider)|
            Q(provider_profile__profile__user=user, rate_by__profile__provider_profile=provider),
            is_active=True
        ).exists():
            return True
        return False

    def create(self, validated_data):
        try:

            rating_instance = ProfileRating.objects.create(
                **validated_data
            )
            return rating_instance
        except Exception as exc:
            raise