from rest_framework import serializers, validators

from .models import Category, Skill
from ..provider_models import ProviderSkill


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "category_id", "name",
            "description", "created_at", "updated_at"
        ]


class SkillSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Skill
        fields = [
            "skill_id", "name", "category",
            "is_active", "created_at", "updated_at"
        ]

class ProviderSkillCreateSerializer(serializers.ModelSerializer):
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.active_objects.all(),
        source="skill"
    )
    class Meta:
        model = ProviderSkill
        fields = [
            "skill_id", "proficiency", 
            "years_used", 'is_primary',
            "description"
        ]

        validators = [
            validators.UniqueTogetherValidator(
                queryset=ProviderSkill.objects.all(),
                fields=['provider_profile', 'skill'],
                message="This skill is already attached to your profile."
            )
        ]

    def validate_years_used(self, value):
        if value > 50:
            raise serializers.ValidationError("Years of experience seems unrealistic.")
        return value

    def validate(self, attrs):
        is_primary = attrs.get("is_primary", False)

        if is_primary:
            user = self.context['request'].user

            primary_count = ProviderSkill.objects.filter(
                provider_profile=user.profile.provider_porfile, is_primary=True
            ).count()

            if primary_count >= 5 and not self.instance: # only on create
                raise serializers.ValidationError({"is_primary": "You can only have 5 primary skills."})
        return attrs
    
    def create(self, validated_data):
        user = self.request.user
        validated_data['provider_profile'] = user.profile.provider_profile

        return super().create(validated_data)

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
            "description",
            "is_primary",
            "created_at",
        ]
