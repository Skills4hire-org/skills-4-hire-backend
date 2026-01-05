from rest_framework import serializers
from .base_model import BaseProfile
from .provider_models import ProviderModel


class BaseProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = BaseProfile
        fields = [
            "gender",
            "bio",
            "display_name",
            "location"
        ]

        def validate_gender(self, value):
            allowed_gender = ["MALE", "FEMALE", "OTHER"]

            if value.upper() not in allowed_gender:
                raise   serializers.ValidationError(f"Only allowed gender is {allowed_gender}")

            return value


class ProviderProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProviderModel
        fields = [ 
            "about",
            "occupation",
            "headline",
            "overview",
            "experience_level",
            "availability",
            "min_charge",
            "max_charge",
            "hourly_pay",
            "features",
            "description",
            "jobs_done",

        ]
        

class ProviderProfileSerializerOut(serializers.ModelSerializer):
    provider_profile =  ProviderProfileSerializer(read_only=True)
    class Meta:
        model = BaseProfile
        fields = [
            "profile_id",
            "gender",
            "bio",
            "display_name",
            "location",
            "provider_profile"
        ]
    


    