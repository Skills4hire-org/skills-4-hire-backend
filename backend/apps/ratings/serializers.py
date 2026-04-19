from django.db import transaction
from rest_framework import serializers

from .core.validators import validate_rating, validate_reviews
from .models import ProfileReview, ProfileRating
from .services.ratings import RatingService
from .services.reviews import ReviewService
from ..authentication.serializers import UserReadSerializer
from ..chats.core.utils import sanitize_message_content
from ..core.utils.py import get_or_none
from ..users.provider_models import ProviderModel

import uuid
import logging

logger = logging.getLogger(__name__)

class ReviewCreateSerializer(serializers.ModelSerializer):
    provider_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = ProfileReview
        fields = [
            "provider_id", 'review'
        ]

    def validate(self, data):
        try:
            isinstance(data['provider_id'], uuid.UUID)
        except Exception as e:
            raise serializers.ValidationError(e)

        return data

    def validate_review(self, value):
        is_valid,message = validate_reviews(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        return sanitize_message_content(value)

    def create(self, validated_data):
        user = self.context['request'].user

        provider = get_or_none(ProviderModel, pk=validated_data['provider_id'])
        if provider is None:
            raise serializers.ValidationError("User profile not found")
        with transaction.atomic():
            try:
                review_service = ReviewService()
                if review_service._dublicate_reviews(user, provider):
                    raise serializers.ValidationError("review found for this user")

                if review_service._cant_review_yourself(user, provider):
                    raise serializers.ValidationError("You cannot review yourself.")
                
                validated_data.pop("provider_id")
                validated_data.update({
                    "provider_profile": provider,
                    "reviewed_by": user
                })

                review_instance = review_service.create_review(validated_data)
            
            except Exception as exc:
                raise serializers.ValidationError(exc)
            
        return review_instance

    @transaction.atomic
    def update(self, instance: ProfileReview, validated_data):
        return super().update(instance, validated_data)

class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileReview
        fields = [
            'review'
        ]
    def validate_review(self, value):
        is_valid,message = validate_reviews(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        return sanitize_message_content(value)

class ReviewDetailSerializer(serializers.ModelSerializer):
    reviewed_by = UserReadSerializer(read_only=True)

    class Meta:
        model = ProfileReview
        fields = [
            "review_id",
            "reviewed_by",
            "review",
            "is_active",
            "created_at",
            "updated_at",
        ]

class ReviewSerializer(serializers.ModelSerializer):
    reviewed_by = UserReadSerializer(read_only=True)
    total_reviews = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProfileReview
        fields = [
            "review_id",
            "reviewed_by",
            "review",
            "is_active",
            "created_at",
            "updated_at",
            "total_reviews"
        ]

class RatingCreateSerializer(serializers.ModelSerializer):
    provider_id = serializers.UUIDField(write_only=True, required=True)
    class Meta:
        model = ProfileRating
        fields = [
            "provider_id", 'rating'
        ]
    def validate(self, data):
        try:
            isinstance(data['provider_id'], uuid.UUID)
        except Exception as exc:
            raise serializers.ValidationError(exc)
        return data

    def validate_rating(self, value):
        is_valid, message = validate_rating(value)
        if not is_valid:
            raise serializers.ValidationError(message)

        return value

    def create(self, validated_data):
        current_user = self.context['request'].user

        provider = get_or_none(ProviderModel, pk=validated_data['provider_id'])
        if provider is None:
            raise serializers.ValidationError("profile not found for provider")
        validated_data.pop("provider_id")
        try:
            with transaction.atomic():
                rating_service = RatingService()
                if rating_service._duplicate_rating(current_user, provider):
                    raise serializers.ValidationError("Duplicate rating. you alrady rated this profile")
                
                if ReviewService()._cant_review_yourself(current_user, provider):
                    raise serializers.ValidationError("You cannot rate yourself")
                
                validated_data.update({
                    "rate_by": current_user,
                    "provider_profile": provider
                })

                new_rating = rating_service.create(validated_data)
        except Exception as exc:
            raise serializers.ValidationError(exc)
        
        return new_rating

class RatingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileRating
        fields = [
            'rating'
        ]
    def validate_rating(self, value):
        is_valid, message = validate_rating(value)
        if not is_valid:
            raise serializers.ValidationError(message)

        return value

class RatingDetailSerializer(serializers.ModelSerializer):
    rate_by = UserReadSerializer(read_only=True)
    class Meta:
        model = ProfileRating
        fields = [
            "rating_id",
            "rate_by",
            "rating",
            "is_active",
            "created_at",
            "updated_at"
        ]

class RatingSerializer(serializers.ModelSerializer):
    rate_by = UserReadSerializer(read_only=True)

    class Meta:
        model = ProfileRating
        fields = [
            "rating_id",
            "rate_by",
            "rating",
            "is_active",
            "created_at",
            "updated_at"
        ]