from rest_framework import serializers, validators

from .models import Category, Skill
from ..provider_models import ProviderSkill


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "category_id", "name", "icon",
            "description", "created_at", "updated_at"
        ]


class SkillSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Skill
        fields = [
            "skill_id", "name", "category", "is_featured",
            "is_active", "created_at", "updated_at"
        ]

class ProviderSkillCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProviderSkill
        fields = [
            "provider_skill_id", "skill",
            "proficiency", "years_used",
            "is_primary", "sort_order",
            "level_of_experience", "description"
        ]
        validators = [
            validators.UniqueTogetherValidator(
                queryset=ProviderSkill.objects.all(),
                fields=['provider_profile', 'skill'],
                message="This skill is already attached to your profile."
            )
        ]
    def validate_years_used(self, value):
        if value > 50:  # Realistic business logic check
            raise serializers.ValidationError("Years of experience seems unrealistic.")
        return value

    def validate(self, attrs):

        if attrs.get('is_primary'):
            provider = self.context['request'].user.profile.provider_profile
            primary_count = ProviderSkill.objects.filter(
                provider_profile=provider, is_primary=True
            ).count()
            if primary_count >= 5 and not self.instance: # only on create
                raise serializers.ValidationError({"is_primary": "You can only have 5 primary skills."})
        return attrs

class ProviderSkillListSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)

    class Meta:
        model = ProviderSkill
        fields = [
            "provider_skill_id",
            "skill",
            "proficiency",
            "years_used",
            "is_primary",
        ]


class ProviderSkillDetailSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)

    class Meta:
        model = ProviderSkill
        fields = [
            "provider_skill_id",
            "skill",
            "proficiency",
            "years_used",
            "level_of_experience",
            "description",
            "is_primary",
            "sort_order",
            "created_at",
            "updated_at",
        ]
