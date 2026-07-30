from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import UserAddress
from .services.address_services import AddressService
# from ..serializers import BaseProfileReadSerializer
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class AddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            "street_address", "apartment",
            "city", "state", "country",
            "postal_code", "is_default"
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

    def create(self, validated_data):
        user = self.context.get("request").user
        user_base_profile = user.profile

        try:
            address = AddressService().create_address(
                user_profile=user_base_profile,
                validated_data=validated_data
            )
            return address
        except Exception as e:
            raise serializers.ErrorDetail(string=str(e), code=400)
        

    def update(self, instance: UserAddress, validated_data: dict):
        user = self.context.get("request").user

        if not instance.user_profile.user == user:
            raise PermissionDenied()
        validated_data.pop("user_profile_id")
        for key, value in validated_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.save(update_fields=[validated_data.keys()])
        return instance

class AddressSerializer(serializers.ModelSerializer):
    user_profile_id = serializers.UUIDField(read_only=True, source="user_profile.pk")
    class Meta:
        model = UserAddress
        fields = [
            "address_id", "user_profile_id",
            "street_address", "apartment",
            "city", "state", "country",
            "postal_code", "is_default"
        ]

class AddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            "address_id", 'created_at',
            "street_address", "apartment",
            "city", "state", "country",
            "postal_code", "is_default"
        ]
        
        