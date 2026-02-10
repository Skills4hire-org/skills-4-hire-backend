from rest_framework import serializers
from ..base_model import Avater

class AvaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avater
        fields = [
            "profile", "avater_id",
            "avater", "description",
            "avater_public_id", "created_at"
        ]

        read_only_fields  = [
            "avater_id", "created_at",
            "profile"
        ]
    default_error_messages = {
        "invalid_profile": "Invalid request. User profile not found."
    }
    def create(self, validated_data):
        request = self.context.get("request")

        user_profile = getattr(request.user, "profile", None)
        if user_profile is None:
            self.fail(invalid_profile=self.error_messages["invalid_profile"])

        avater = Avater.objects.create(profile=user_profile, **validated_data)
        return avater