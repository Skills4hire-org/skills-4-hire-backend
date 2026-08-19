from typing import Any

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
        if value and not UserAddress().validate_postal_code(value):
            raise serializers.ValidationError("postal code is not valid")
        return value

    def validate(self, data):
        for value in data.values():
            if isinstance(value, str):
                value.strip().title()
        return data


    def create(self, validated_data: Any) -> Any:
        street_address = validated_data.get('street_address')
        apartment = validated_data.get("apartment")
        city = validated_data.get("city")
        state = validated_data.get("state")
        country = validated_data.get("country")
        postal_code = validated_data.get("postal_code")

        address, created = UserAddress.objects.update_or_create(
            user_profile=self.context['request'].user.profile,
            street_address=street_address,
            apartment=apartment,
            city=city,
            state=state, country=country,
            postal_code=postal_code,
            defaults=validated_data
        )

        return address

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
        
        