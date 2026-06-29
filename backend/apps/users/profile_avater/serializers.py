import validators
from rest_framework import serializers

from .models import Avatar


class AvatarCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = [
            'avatar', 'avatar_public_id', 'description'
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
        base_profile = self.context.get("profile", None)
        try:
            avatar = Avatar.objects.update_or_create(profile=base_profile, defaults=validated_data)
        except Exception as e:
            raise serializers.ValidationError(e)
        return avatar


class AvatarDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = [
            "avatar_id","description", 'avatar',
            "avatar_public_id",'created_at'
        ]



