from rest_framework import serializers
from .base_model import BaseProfile, Address, Avater
from .provider_models import ProviderModel
from .client_models import ClientModel


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

class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta: 
        model = ClientModel
        fields = [
            "organisation_name",
            "organisation_type",
            "industry",
            "website",
            "total_hires",
        ]


    
class OnboardingSerializer(serializers.Serializer):

    """
    Handles onboarding user roles 
    """

    role = serializers.ChoiceField(choices=["SERVICE_PROVIDER", "CLIENT", "BOTH"], required=True)

    def validate_role(self, value:str):
        allowed_roles = ["SERVICE_PROVIDER", "CLIENT", "BOTH"]
        if value.upper() not in allowed_roles:
            raise serializers.ValidationError(detail=f"Bad Request: allowed roles: {allowed_roles}", code=400)
        
        return value


class BaseProfileUpdateSerializer(serializers.Serializer):

    gender = serializers.CharField(max_length=200)
    bio = serializers.CharField(max_length=1000)
    location = serializers.CharField(max_length=200)

    provider_profile = ProviderProfileSerializer(required=False)
    client_profile = ClientProfileSerializer(required=False)
 
    def validate_gender(self, value):
            allowed_gender = ["MALE", "FEMALE", "OTHER"]

            if value.upper() not in allowed_gender:
                raise   serializers.ValidationError(f"Only allowed gender is {allowed_gender}")

            return value

    def validate(self, data):
        
        request = self.context["request"]

        if "provider_profile" in data and request.user.active_role != "SERVICE_PROVIDER":
            raise serializers.ValidationError(
                "User is not a Provider"
            )

        if "client_profile" in data and request.user.active_role != "CLIENT":
            raise serializers.ValidationError(
                "User is Not a CLient"
            )

        return data

    


class AddresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "address_id",
            "line1",
            "line2",
            "city",
            "state",
            "postal_code",
            "country",
            "created_at"
        ]


class AvaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avater
        fields = [
            "avater_id",
            "avater",
            "description",
            "avater_public_id",
            "created_at"
        ]

class BaseProfileReadSerializer(serializers.ModelSerializer):

    provider_profile = ProviderProfileSerializer(read_only=True)
    client_profile = ClientProfileSerializer(read_only=True)
    address = AddresSerializer(many=True, read_only=True)
    avaters = AvaterSerializer()
    active_role = serializers.SerializerMethodField()
    
    class Meta:
        model = BaseProfile
        fields = [
            "profile_id",
            "gender",
            "bio",
            "display_name",
            "active_role",
            "location",
            "is_verified",
            "created_at",
            "provider_profile",
            "client_profile",
            "address",
            "avaters"
        ]

    def get_active_role(self, obj):
        return obj.user.active_role