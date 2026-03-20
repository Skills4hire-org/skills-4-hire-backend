from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import UserAddress, UserModel
from .services.address_services import AddressService
# from ..serializers import BaseProfileReadSerializer


class AddressCreateSerializer(serializers.ModelSerializer):
    user_profile_id = serializers.UUIDField(write_only=True, required=False)
    class Meta:
        model = UserAddress
        fields = [
            "address_id", "user_profile_id",
            "street_address", "apartment",
            "city", "state", "country",
            "postal_code", "is_default"

        ]

    def validate_postal_code(self, value):
        if not UserAddress().validate_postal_code(value.strip()):
            raise serializers.ValidationError("postal code is not valid")
        return value

    def validated(self, data):
        user = self.context.get("request").user
        user_base_profile = user.profile
        if AddressService().address_already_exists(
            user_base_profile, data['postal_code']
        ):
            raise serializers.ValidationError("Address with this postal code already exists in you profile")
        for value in data.values():
            if isinstance(value, str):
                value.strip().title()
        return data

    def create(self, validated_data):
        user = self.context.get("request").user

        if "user_profile_id" in  validated_data:
            user_base_profile = UserModel.objects.get(email__iexact=user.email, is_active=True)
            validated_data.pop("user_profile_id")
        else:
            user_base_profile = user.profile

        try:
            address = AddressService().create_address(
                user_profile=user_base_profile,
                validated_data=validated_data
            )
        except Exception as e:
            raise serializers.ErrorDetail(string=str(e), code=400)
        return address

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
    # user_profile = BaseProfileReadSerializer()

    class Meta:
        model = UserAddress
        fields = [
            "address_id", "user_profile",
            "street_address", "apartment",
            "city", "state", "country",
            "postal_code", "is_default"
        ]
        
        