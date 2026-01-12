from rest_framework import serializers
from .base_model import BaseProfile, Address, Avater, SkillCategory
from .provider_models import ProviderModel, ProviderSkills
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
        if not hasattr(obj, "user"):
            raise serializers.ValidationError("This user has no user object")

        return obj.user.active_role
    
class ProviderSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderSkills
        fields = [
            "skill_id",
            "efficiency",
            "level_of_experience",
            "work_refrences",
            "created_at"
        ]

    def validate_level_of_experience(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Level of experience must be a number")
        if int(value) < 0:
            raise serializers.ValidationError("Level of experience must be a positive number")
        return value
    

    def validate_efficiency(self, value):
        allowed_efficiency = ["BEGINEER", "INTERMIDIATE", "EXPERT"]

        if value.upper() not in allowed_efficiency:
            raise serializers.ValidationError(f"Only allowed efficiency are {allowed_efficiency}")

        return value

    def create(self, validated_data):
        """
        Create a new skill for the provider \n
        Raise ValidationError if skill does not exist or user is not a provider \n
        return the created skill
        """
        request = self.context["request"]
        skill_name = self.context["skill_name"]

        if not SkillCategory.objects.filter(name=skill_name).exists():
            raise serializers.ValidationError("Skill does not exist")
        profile = request.user.profile


        if not hasattr(profile, "provider_profile"):
            raise serializers.ValidationError("User is not a provider")

        provider_profile = profile.provider_profile

        skill, created = ProviderSkills.objects.get_or_create(
            profile=provider_profile,
            skill=skill_name,
            defaults={
                "efficiency": validated_data.get("efficiency"),
                "level_of_experience": validated_data.get("level_of_experience"),
                "work_reference": validated_data.get("work_reference"),
            }
        )

        if not created:
            raise serializers.ValidationError("Skill already exists for this provider")

        return skill