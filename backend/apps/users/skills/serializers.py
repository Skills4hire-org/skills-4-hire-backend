from rest_framework import serializers

from django.contrib.auth import get_user_model

from ..provider_models import ProviderSkills, Category
from ..serializers import validate_request


UserModel = get_user_model()

class SkillSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source="category")
    class Meta:
        model = ProviderSkills
        fields = [
            "category", "efficiency", 
            "level_of_experience",
            "description", "work",
            "is_primary",
        ]

        read_only_fields = ["skill_id", "is_active", "created_at"]

    def validate(self, data):
        experience = data.get("level_of_experience")
        efficiency = data.get("efficiency")
        validate_request(self.context["request"])
        if not experience.isdigit():
            raise serializers.ValidationError("Level of experience must be a number")
        if int(experience) < 0:
            raise serializers.ValidationError("Level of experience must be a positive number")
        if efficiency not in ProviderSkills.EfficiencyStatus.choices:
            raise serializers.ValidationError(f"Invalid data. Provided efficiency is not allowed: {ProviderSkills.EfficiencyStatus.choices}")
        return data

    def create(self, validated_data):
        """
        Create a new skill for the provider \n
        Raise ValidationError if skill does not exist or user is not a provider \n
        return the created skill
        """
        request = self.context["request"]

        profile = request.user.profile if hasattr(request.user, "profile") else None
        if profile is None:
            raise serializers.ValidationError("Invalid: No profile instance for user")
        
        if not hasattr(profile, "provider_profile"):
            raise serializers.ValidationError("User is not a provider")
        
        if request.user.active_role != UserModel.RoleChoices.SERVICE_PROVIDER:
            raise serializers.ValidationError("User is not a provider")
        
        provider_profile = profile.provider_profile
        skill = ProviderSkills.objects.create(profile=provider_profile, **validated_data   
        )

        return skill
    
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "skill_category_id", "name",
            "category", "slug",
            "created_at"
        ]


class SkillReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    class Meta:
        model = ProviderSkills
        fields = [
            "skill_id", "category",
            "efficiency", "level_of_experience",
            "description", "work",
            "is_primary", "is_active",
            "created_at"
        ]
