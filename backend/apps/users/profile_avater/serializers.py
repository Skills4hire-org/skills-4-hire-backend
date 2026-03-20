import validators
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from .models import Avatar
from ..base_model import BaseProfile
from ...core.utils.py import get_or_none


class AvatarCreateSerializer(serializers.ModelSerializer):
    base_profile_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Avatar
        fields = [
            'avatar_id', "base_profile_id",
            'avatar', 'avatar_public_id',
            'description'
        ]

    default_error_messages = {
        "invalid_profile": "Invalid request. User profile not found.",
        "invalid_url": "avatar profile is invalid"
    }

    def validate_avatar(self, value):
        if not validators.url(value):
            self.fail('invalid_url')
        return value

    def create(self, validated_data):

        base_profile = None

        if "base_profile_id" in validated_data:
            base_pk = validated_data.pop("base_profile_id")
            base_profile = get_or_none(BaseProfile, pk=base_pk)
            if base_profile is None:
                raise NotFound("profile not found")
        else:
            user = self.context.get("request").user
            base_profile = user.profile

        try:
            avatar = Avatar.objects.create(profile=base_profile, **validated_data)
        except Exception as e:
            raise Exception(e)

        return avatar

    def update(self, instance, validated_data):
        user = self.context.get("request").user
        validated_data.pop("base_profile_id")
        for key, value in validated_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.save(update_fields=[validated_data.keys()])
        return instance


class AvatarDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = [
            "avatar_id", "profile",
            "description", 'avatar',
            "avatar_public_id", "is_active",
            'created_at', 'updated_at'
        ]



