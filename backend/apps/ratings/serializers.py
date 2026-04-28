from django.db import transaction
from rest_framework import serializers

from .core.validators import validate_rating, validate_reviews
from .models import ProfileReview
from .services.reviews import ReviewService
from ..authentication.serializers import UserReadSerializer
from ..chats.core.utils import sanitize_message_content
from ..core.utils.py import get_or_none
from ..users.provider_models import ProviderModel
from ..users.serializers.profiles import ProviderProfilePublicSerializer

import uuid
import logging

logger = logging.getLogger(__name__)

class ReviewCreateSerializer(serializers.ModelSerializer):
    provider_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = ProfileReview
        fields = [
            "provider_id", 'reviews', 
            'ratings'
        ]

    def validate(self, data):
        try:
            isinstance(data['provider_id'], uuid.UUID)
        except Exception as e:
            raise serializers.ValidationError(e)

        return data

    def validate_reviews(self, value):
        is_valid,message = validate_reviews(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        return sanitize_message_content(value)
    
    def validate_ratings(self, value):
        valid, _ = validate_rating(value)
        if not valid:
            raise serializers.ValidationError(_)
        return value

    def create(self, validated_data):
        user = self.context['request'].user

        provider = get_or_none(ProviderModel, pk=validated_data['provider_id'])

        if provider is None:
            raise serializers.ValidationError("User profile not found")
        
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
        with transaction.atomic():
            try:
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
            'reviews', 'ratings'
        ]
    def validate_reviews(self, value):
        is_valid,message = validate_reviews(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        return sanitize_message_content(value)
    
    def validate_ratings(self, value):
        valid, _ = validate_rating(value)
        if not valid:
            raise serializers.ValidationError(_)
        return value
    
class ReviewDetailSerializer(serializers.ModelSerializer):
    reviewed_by = UserReadSerializer(read_only=True)
    provider_profile = ProviderProfilePublicSerializer(read_only=True)

    class Meta:
        model = ProfileReview
        fields = [
            "review_id",
            "reviewed_by",
            "provider_profile",
            "reviews",
            'ratings',
            "is_active",
            "created_at",
            "updated_at",
        ]
