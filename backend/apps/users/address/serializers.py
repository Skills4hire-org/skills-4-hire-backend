from rest_framework import serializers
from .models import UserAddress
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class AddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            "street_address", "apartment",
            "city", "state", "country",
            "postal_code",
        ]

    def validate_postal_code(self, value):
        if not UserAddress().validate_postal_code(value.strip()):
            raise serializers.ValidationError("postal code is not valid")
        return value

    def validate(self, data):
        for value in data.values():
            if isinstance(value, str):
                value.strip().title()
        return data


class AddressSerializer(serializers.ModelSerializer):
    user_profile_id = serializers.UUIDField(read_only=True, source="user_profile.pk")
    class Meta:
        model = UserAddress
        fields = [
            "address_id", "user_profile_id",
            "street_address", "apartment",
            "city", "state", "country",
            "postal_code",
        ]

class AddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            "address_id", 'created_at',
            "street_address", "apartment",
            "city", "state", "country",
            "postal_code",
        ]
        
        