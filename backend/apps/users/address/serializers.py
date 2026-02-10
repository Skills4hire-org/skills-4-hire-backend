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

    def create(self, validated_data):
        request = self.context.get("request")
        profile_pk = self.context.get("profile_pk")

        user_profile = getattr(request.user, "profile")
        if user_profile.pk != profile_pk:
            raise PermissionDenied()
        address = Address.objects.create(profile=user_profile, **validated_data)
        return address
        
        