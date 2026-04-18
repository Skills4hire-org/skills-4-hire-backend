
from django.db import transaction

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

import validators

from ..base_model import BaseProfile
from ..customer_models import CustomerModel
from ..profile_avater.serializers import AvatarDetailSerializer
from ..profile_services.customer_profile import CustomerService
from ..profile_services.provider_profile import ProviderProfileServices
from ..profile_services.utils import get_profile_avatar
from ..provider_models import ProviderModel

def save_base_profile_with_serializer(base_profile, validated_data, request):
    serializer = BaseProfileCreateSerializer(
        base_profile, data=validated_data, partial=True,
        context={"request": request})

    serializer.is_valid(raise_exception=True)

    serializer.save()

class BaseProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseProfile
        fields = [
            "gender", "display_name",
            "country", "city", "bio"
        ]

    def validate_bio(self, value):
        if len(value) > 2000:
            raise serializers.ValidationError("exceeded max length")
        return value

    def validate_gender(self, value):
        if value not in BaseProfile.GenderChoices.choices:
            raise serializers.ValidationError("Invalid gender")
        return value.strip()

    def validate_display_name(self, value):
        user = self.context.get("request").user
        if value is None:
            value = user.full_name or user.username
        return value.title()

    def validate(self, data):
        for value in data.values():
            value = value.strip()
        return data

    def update(self, instance: BaseProfile, validated_data: dict):

        if not isinstance(instance, BaseProfile):
            raise serializers.ValidationError("Invalid profile type")

        user = self.context.get("request").user
        if instance.user != user:
            raise PermissionDenied()

        for key, value in validated_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.save()
        return instance

class BaseProfileListSerializer(serializers.ModelSerializer):
    avater = AvatarDetailSerializer(read_only=True)

    class Meta:
        model = BaseProfile
        fields = [
            "gender", "display_name",
            "country", "city", "created_at", "avater"
        ]

class ProviderProfileUpdateCreateSerializer(serializers.ModelSerializer):

    profile = BaseProfileCreateSerializer(required=False)

    class Meta:
        model = ProviderModel
        fields = [
            "profile_id", "professional_title",
            "headline", "overview", "profile",
            "experience_level", "availability",
            "min_charge", "max_charge", "hourly_pay",
            "years_of_experience", "open_to_full_time",
            "jobs_done",
        ]

    def validate(self, data):
        for value in data.values():
            if isinstance(value, str):
                value.strip()

        return data

    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("request").user
        base_profile = user.profile
        if "profile" in validated_data:
            user_base_profile_data = validated_data.get("profile")
            save_base_profile_with_serializer(
                base_profile, user_base_profile_data, self.context.get("request"))
            validated_data.pop("profile")
        try:
            user_profile = ProviderProfileServices()\
                .create_provider_profile(base_profile, validated_data)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return user_profile

    def update(self, instance, validated_data):
        user = self.context.get("request").user
        if instance.profile.user != user:
             raise PermissionDenied()

        if "profile" in validated_data:
            base_profile_data = validated_data.get("profile")
            save_base_profile_with_serializer(
                instance.profile, base_profile_data, self.context.get("request"))

            validated_data.pop("profile")

        updated_profile = super().update(instance, validated_data)
        return updated_profile

class ProviderProfileDetailSerializer(serializers.ModelSerializer):

        profile = BaseProfileListSerializer(read_only=True)
        profile_avatar = serializers.SerializerMethodField()

        class Meta:
            model = ProviderModel
            fields = [
                "provider_id", "professional_title",
                "headline", "overview", "profile",
                "experience_level", "availability",
                "min_charge", "max_charge", "hourly_pay",
                "years_of_experience", "open_to_full_time",
                "jobs_done", "is_featured", "is_top_rated",
                'is_active', "created_at", "updated_at", "profile_avatar"

            ]

        def get_profile_avatar(self, obj):
            avatar = get_profile_avatar(profile=obj)
            if avatar is None:
                return None
            return AvatarDetailSerializer(avatar).data

class ProviderProfilePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderModel
        fields = [
            "provider_id", "professional_title",
            "headline", "overview", "experience_level",
            "availability", "min_charge", "max_charge", "hourly_pay",
            "years_of_experience", "open_to_full_time", "is_top_rated",
        ]

class CustomerCreateUpdateSerializer(serializers.ModelSerializer):

    profile = BaseProfileCreateSerializer(required=False)
    class Meta:
        model = CustomerModel
        fields = [
            "customer_id", "profile",
            "website", "city", "country",
            "industry_name"
        ]

    def validate_website(self, value):
        if not validators.url(value):
            raise serializers.ValidationError("Invalid website")
        return value

    def validate(self, data):
        for key, value in data.items():
            if key == "website":
                continue
            if isinstance(value, str):
                value.strip().title()
        return data


    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("request").user
        base_profile = user.profile
        if "profile" in validated_data:
            user_base_profile_data = validated_data.get("profile")
            save_base_profile_with_serializer(
                base_profile, user_base_profile_data,
                self.context.get("request")
            )
            validated_data.pop("profile")
        try:
            user_profile = CustomerService() \
                .create_customer(base_profile, validated_data)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return user_profile

    def update(self, instance, validated_data):
        user = self.context.get("request").user
        if instance.profile.user != user:
            raise PermissionDenied()

        if "profile" in validated_data:
            base_profile_data = validated_data.get("profile")
            save_base_profile_with_serializer(
                instance.profile, base_profile_data,
                self.context.get("request")
            )

            validated_data.pop("profile")

        updated_profile = super().update(instance, validated_data)
        return updated_profile

class CustomerProfileDetailSerializer(serializers.ModelSerializer):
    profile = BaseProfileListSerializer()
    profile_avatar = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()

    class Meta:
        model = CustomerModel
        fields = [
            "customer_id", 'website',
            "profile", "industry_name",
            "created_at", "is_active", "city",
            "country", "is_verified", "profile_avatar"
        ]

    def get_country(self, obj):
        return obj.get_country()

    def get_profile_avatar(self, obj):
        avatar = get_profile_avatar(profile=obj)
        if avatar is None:
            return None
        return AvatarDetailSerializer(avatar).data

class CustomerProfilePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerModel
        fields = [
            "customer_id", "profile",
            "industry_name", "website",
            "created_at", "is_verified"
        ]


