from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from ..base_model import Address

class AddresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "address_id", "profile",
            "line1", "line2",
            "city", "state",
            "postal_code", "country",
            "created_at"
        ]

        read_only_fields = [
            "address_id", "profile",
            "created_at"
        ]

    def validate(self, data):
        user = self.context.get("request")["user"]
        if Address.objects.filter(profile=user.profile, postal_code=data["postal_code"]).exists():
            raise serializers.ValidationError("This Address Already Exist in your Profile")
        fields_to_capitalize = ("city", "state", "country")
        for value in fields_to_capitalize:
            data[value].title()
        return  data

    def create(self, validated_data):
        request = self.context.get("request")
        profile_pk = self.context.get("profile_pk")

        user_profile = getattr(request.user, "profile")
        if user_profile.pk != profile_pk:
            raise PermissionDenied()
        address = Address.objects.create(profile=user_profile, **validated_data)
        return address
        
        