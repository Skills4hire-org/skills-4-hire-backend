from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import ProfileReview, ProfileRating
from .utils.profiles import get_user_with_profile

import logging

logger = logging.getLogger(__name__)


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileReview
        fields = [
            "review"
        ]

    def validate_review(self, value):

        if len(value.strip()) < 2:
            raise serializers.ValidationError("Review must be at least 2 characters long.")
        return value.strip()
    
    def create(self, validated_data):
        request, profile_obj = get_user_with_profile(self)
        review = ProfileReview.objects.create(profile=profile_obj, reviewed_by=request.user, **validated_data)

        return review
    

    def update(self, instance, validated_data):
        instance.review = validated_data.get("review", instance.review)
        instance.save(update_fields=["review"])
        return instance
        

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileRating
        fields = [
            "rating"
        ]

    def validate_rating(self, value):
        value = value.strip()
        if not isinstance(value, int):
            raise serializers.ValidationError("Rating must be an integer.")
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def create(self, validated_data):
        request, profile_obj = get_user_with_profile(self)
        rating = ProfileRating(rate_by=request.user, profile=profile_obj, **validated_data)
        try:
           rating.full_clean()
        except ValidationError as e:
            logger.error("Validation Errors:")
            for field, errors in e.message_dict.items():
                print(f"- {field}: {', '.join(errors)}")          
        else:
            rating.save()
            logger.info("Rating instance saved successfully")

        return rating
    