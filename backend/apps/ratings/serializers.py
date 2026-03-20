from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .core.validators import validate_data, validate_rating, validate_reviews, privileged_to_rate_or_review
from .models import ProfileReview, ProfileRating
from .services.ratings import RatingService
from .services.reviews import ReviewService

import logging

from .utils.profiles import customer_email_or_provider_email_or_none
from ..authentication.serializers import UserReadSerializer
from ..chats.core.utils import sanitize_message_content
from ..core.utils.py import get_or_none
from ..users.customer_models import CustomerModel
from ..users.provider_models import ProviderModel
# from ..users.serializers import CustomerProfileSerializer, ProviderProfileSerializer


logger = logging.getLogger(__name__)


class ReviewCreateSerializer(serializers.ModelSerializer):
    provider_profile_id = serializers.UUIDField(write_only=True, required=False)
    customer_profile_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = ProfileReview
        fields = [
            "review_id",
            "is_active",
            "created_at",
            "updated_at",
            "review",
            "provider_profile_id",
            "customer_profile_id"
        ]
        read_only_fields = [
            "review_id",
            "is_active",
            "created_at",
            "updated_at"
        ]

    def validate(self, data):
        is_valid, message = validate_data(data)
        if not is_valid:
            raise serializers.ValidationError(message)
        return data

    def validate_review(self, value):
        is_valid,message = validate_reviews(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        return sanitize_message_content(value)

    @transaction.atomic
    def create(self, validated_data):

        current_user = self.context.get('request').user

        service = ReviewService(review=validated_data['review'], reviewed_by=current_user)

        if "provider_profile_id" in validated_data:
            pk = validated_data["provider_profile_id"]
            validated_data.pop("provider_profile_id")

            provider_profile = get_or_none(ProviderModel, pk=pk)
            if not privileged_to_rate_or_review(current_user=current_user, user_profile=provider_profile):
                raise PermissionDenied("You cannot review your self.")

            rating = service.create_review(user_profile=provider_profile, validated_data=validated_data)
        elif "customer_profile_id" in validated_data:
            pk = validated_data["customer_profile_id"]
            validated_data.pop("customer_profile_id")

            customer_profile = get_or_none(CustomerModel, pk=pk)

            if not privileged_to_rate_or_review(current_user=current_user, user_profile=customer_profile):
                raise  PermissionDenied("You cannot review your self.")

            rating = service.create_review(user_profile=customer_profile, validated_data=validated_data)
        else:
            raise serializers.ValidationError("Wrong profile")

        return rating

    @transaction.atomic
    def update(self, instance: ProfileReview, validated_data):
        current_user = self.context.get("request").user
        review = validated_data.get("review", "")
        if not instance.is_able_modify(current_user):
            raise serializers.ValidationError("can not update this view")

        instance.review = review
        instance.save(update_fields=['review'])
        return instance


class ReviewDetailSerializer(serializers.ModelSerializer):
    # customer_profile = CustomerProfileSerializer(read_only=True)
    # provider_profile = ProviderProfileSerializer(read_only=True)
    reviewed_by = UserReadSerializer(read_only=True)

    class Meta:
        model = ProfileReview
        fields = [
            "review_id",
            "customer_profile",
            "provider_profile",
            "reviewed_by",
            "review",
            "is_active",
            "created_at",
            "updated_at"
        ]

class ReviewSerializer(serializers.ModelSerializer):
    customer_email = serializers.SerializerMethodField()
    provider_email = serializers.SerializerMethodField()
    reviewed_by = serializers.CharField(source="reviewed_by.email", read_only=True)

    class Meta:
        model = ProfileReview
        fields = [
            "review_id",
            "customer_email",
            "provider_email",
            "reviewed_by",
            "review",
            "is_active",
            "created_at",
            "updated_at"
        ]

    def get_customer_email(self, obj):
        is_valid, email = customer_email_or_provider_email_or_none(obj, "customer")
        if is_valid:
            return email
        return None

    def get_provider_email(self, obj):
        is_valid, email = customer_email_or_provider_email_or_none(obj, "provider")
        if is_valid:
            return email
        return None

class RatingCreateSerializer(serializers.ModelSerializer):
    provider_profile_id = serializers.UUIDField(write_only=True, required=False)
    customer_profile_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = ProfileRating
        fields = [
            "rating_id",
            "is_active",
            "created_at",
            "updated_at",
            "rating",
            "provider_profile_id",
            "customer_profile_id"
        ]
        read_only_fields = [
            "rating_id",
            "is_active",
            "created_at",
            "updated_at"
        ]
    def validate(self, data):
        is_valid, message = validate_data(data)
        if not is_valid:
            raise serializers.ValidationError(message)
        return data

    def validate_rating(self, value):
        is_valid, message = validate_rating(value)
        if not is_valid:
            raise serializers.ValidationError(message)

        return value

    @transaction.atomic
    def create(self, validated_data):

        current_user = self.context.get('request').user

        service = RatingService(rating=validated_data['rating'], rate_by=current_user)

        if "provider_profile_id" in validated_data:
            pk=validated_data["provider_profile_id"]
            validated_data.pop("provider_profile_id")

            provider_profile = get_or_none(ProviderModel, pk=pk)
            if not privileged_to_rate_or_review(current_user=current_user, user_profile=provider_profile):
                raise PermissionDenied("You cannot rate your self")

            rating = service.create_rating(validated_data, provider_profile)

        elif "customer_profile_id" in validated_data:
            pk=validated_data["customer_profile_id"]
            validated_data.pop("customer_profile_id")

            customer_profile = get_or_none(CustomerModel, pk=pk)

            if not privileged_to_rate_or_review(current_user=current_user, user_profile=customer_profile):
                raise PermissionDenied("You cannot rate your self")

            rating = service.create_rating(validated_data, customer_profile)

        else:
            raise serializers.ValidationError("Wrong profile")

        return rating

    @transaction.atomic
    def update(self, instance: ProfileRating, validated_data):
        current_user = self.context.get("request").user
        rating = validated_data.get("rating", "")
        if not instance.is_able_modify(current_user):
            raise serializers.ValidationError("can not update this view")

        instance.rating = rating
        instance.save(update_fields=['rating'])
        return  instance

class RatingDetailSerializer(serializers.ModelSerializer):
    # customer_profile = CustomerProfileSerializer(read_only=True)
    # provider_profile = ProviderProfileSerializer(read_only=True)
    rate_by = UserReadSerializer(read_only=True)
    class Meta:
        model = ProfileRating
        fields = [
            "rating_id",
            "customer_profile",
            "provider_profile",
            "rate_by",
            "rating",
            "is_active",
            "created_at",
            "updated_at"
        ]

class RatingSerializer(serializers.ModelSerializer):
    provider_email = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    rate_by = serializers.CharField(source="rate_by.email")

    class Meta:
        model = ProfileRating
        fields = [
            "rating_id",
            "customer_email",
            "provider_email",
            "rate_by",
            "rating",
            "is_active",
            "created_at",
            "updated_at"
        ]

    def get_provider_email(self, obj):
        is_valid, email = customer_email_or_provider_email_or_none(obj, "provider")
        if is_valid:
            return email
        return None

    def get_customer_email(self, obj):
        is_valid, email = customer_email_or_provider_email_or_none(obj, "customer")
        if is_valid:
            return email
        return None