
from django.db import transaction
from django.db.models import Avg, Count

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

import validators

from ..base_model import BaseProfile, WorkImages
from ..customer_models import CustomerModel
from ..profile_avater.serializers import AvatarDetailSerializer
from ..profile_services.customer_profile import CustomerService
from ..profile_services.provider_profile import ProviderProfileServices
from ..profile_services.utils import get_profile_avatar
from ..provider_models import ProviderModel
from ..services.models import ServiceAttachment, ServiceCategory
from ..skills.serializers import ProviderSkillListSerializer

def save_base_profile_with_serializer(base_profile, validated_data, request):
    serializer = BaseProfileCreateSerializer(
        base_profile, data=validated_data, partial=True,
        context={"request": request})

    serializer.is_valid(raise_exception=True)

    serializer.save()


class WorkImagesSerializer(serializers.Serializer):
    class Meta:
        model = WorkImages
        fields = [
            "image_url", "description"
        ]

    def validate_image_url(self, value):
        if value and not validators.url(value):
            raise serializers.ValidationError("Invalid image URL")
        return value
    
    def validate_description(self, value):
        if value and len(value) > 255:
            raise serializers.ValidationError("Description exceeded max length")
        return value.strip().title()
    
    def create(self, validated_data):
        return super().create(validated_data)

class BaseProfileCreateSerializer(serializers.ModelSerializer):
    work_images = WorkImagesSerializer(many=True, required=False, read_only=True)
    category_interest = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(), required=False, allow_null=True,
        many=True
    )
    class Meta:
        model = BaseProfile
        fields = [
            "gender", "display_name", "country", 
            "city", "bio", "location", "work_images", 
            "category_interest", "years_of_experience", "is_certified",
            "place_of_work", "phone_number", "nin", "date_of_birth",
            "drivers_lisence", "passport", "certificates"
        ]
    
    
    def validate_nin(self, value):
        if value and len(value) != 11:
            raise serializers.ValidationError("Invalid NIN")
        return value


    def validate_bio(self, value):
        if len(value) > 1_000:
            raise serializers.ValidationError("exceeded max length")
        return value

    def validate_gender(self, value):
        if value not in BaseProfile.GenderChoices.values:
            raise serializers.ValidationError("Invalid gender")
        return value.strip()

    def validate_display_name(self, value):
        user = self.context.get("request").user
        if value is None:
            value = user.full_name or user.username
        return value.title()

    def update(self, instance: BaseProfile, validated_data: dict):
        work_images_data = validated_data.pop("work_images", None)

        user = self.context.get("request").user
        if instance.user != user:
            raise PermissionDenied("You do not have permission to update this profile.")

        if work_images_data is not None:
            serializer = WorkImagesSerializer(data=work_images_data, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(profile=instance)

        validated_data['user'] = instance.user
        return super().update(instance, validated_data)

class BaseProfileListSerializer(serializers.ModelSerializer):
    avatar = AvatarDetailSerializer(read_only=True)
    professional_title = serializers.SerializerMethodField()
    provider_id = serializers.SerializerMethodField()
    customer_id = serializers.SerializerMethodField()
    class Meta:
        model = BaseProfile
        fields = [
            "gender", "display_name", "professional_title", "trust_score",
            "country", "city", "created_at", "avatar", 'user',
            "customer_id", "provider_id"
        ]

    def get_provider_id(self, obj):
        user = obj.user
        if user.is_provider:
            return str(obj.provider_profile.provider_id)
        return None
    
    def get_customer_id(self, obj):
        user = obj.user
        if user.is_customer:
            return str(obj.customer_profile.customer_id)
        return None
    
    def get_professional_title(self, obj):
        user = obj.user
        if not user.is_provider:
            return None
        return obj.provider_profile.professional_title
    
class ProviderProfileUpdateCreateSerializer(serializers.ModelSerializer):

    profile = BaseProfileCreateSerializer(required=False)

    class Meta:
        model = ProviderModel
        fields = [
            "professional_title", "headline", 
            "overview", "profile","experience_level", 
            "availability",
        ]

    def validate(self, data):
        for value in data.values():
            if isinstance(value, str):
                value.strip()
        return data

    def update(self, instance, validated_data):
        user = self.context.get("request").user
        if instance.profile.user != user:
             raise PermissionDenied()

        profile = getattr(user, "profile", None)
        if profile is None:
            raise serializers.ValidationError("profile not found for provider")

        if "profile" in validated_data:
            profile_data = validated_data.pop('profile')
            serializer = BaseProfileCreateSerializer(profile, data=profile_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
        updated_profile = super().update(instance, validated_data)
        return updated_profile

class ProviderProfileDetailSerializer(serializers.ModelSerializer):
        profile = BaseProfileListSerializer(read_only=True)
        endorsement_count = serializers.SerializerMethodField()
        posts = serializers.SerializerMethodField()
        comments = serializers.SerializerMethodField()
        images  = serializers.SerializerMethodField()
        skills = ProviderSkillListSerializer(many=True)

        class Meta:
            model = ProviderModel
            fields = [
                "provider_id", "professional_title",
                "headline", "overview", "profile",
                "created_at", "endorsement_count", "posts",
                'comments', 'images', "skills"
            ]

        def get_images(self, obj):
            from ..services.serializers import ServiceAttachmentSerializer
            images = ServiceAttachment.objects.filter(service__profile=obj)
            return ServiceAttachmentSerializer(images, many=True).data

        def get_comments(self, obj):
            from ...posts.serializers.read import CommentListSerializer
            user = obj.profile.user
            user_comments = user.comments.filter(is_active=True, is_deleted=False)
            if len(user_comments) < 1:
                return None
            
            serializer = CommentListSerializer(user_comments, many=True, context={"request": self.context['request']})
            return serializer.data

        def get_posts(self, obj):
            from ...posts.serializers.read import PostDetailSerializer
            user = obj.profile.user
            user_posts = user.posts.filter(is_active=True, is_deleted=False)
    
            serializer = PostDetailSerializer(user_posts, many=True, context={'request': self.context['request']})
            return serializer.data

        def get_endorsement_count(self, obj):
            endorsement = obj.receiver_endorse.filter(is_active=True)
            if len(endorsement) < 1:
                return 0
            
            total_endorsement = endorsement.aggregate(total=Count("provider"))
            return total_endorsement['total']

class ProviderProfilePublicSerializer(serializers.ModelSerializer):
    profile = BaseProfileListSerializer(read_only=True)
    avg_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    skills = ProviderSkillListSerializer(read_only=True,  many=True)

    class Meta:
        model = ProviderModel
        fields = [
            "provider_id", "profile", "professional_title",
            "avg_rating", "total_reviews", "skills", 
            "overview", "headline"
        ]

    def get_avg_rating(self, obj: ProviderModel):
        
        profile_reviews = obj.reviews.filter(is_active=True)
        if len(profile_reviews) < 1:
            return 0
        avg_rating = profile_reviews.aggregate(avg=Avg("ratings"))
        return avg_rating['avg']
        
    def get_total_reviews(self, obj):
        profile_reviews = obj.reviews.filter(is_active=True)
        if len(profile_reviews) < 1:
            return 0
        total_reviews= profile_reviews.aggregate(total=Count("reviews"))
        return total_reviews['total']

class CustomerCreateUpdateSerializer(serializers.ModelSerializer):

    profile = BaseProfileCreateSerializer(required=False)
    class Meta:
        model = CustomerModel
        fields = [
            "customer_id", "profile",
            "website", "city", "country",
            "industry_name"
        ]

    def validate_website(self, value):
        if not validators.url(value):
            raise serializers.ValidationError("Invalid website")
        return value

    def validate(self, data):
        for key, value in data.items():
            if key == "website":
                continue
            if isinstance(value, str):
                value.strip().title()
        return data


    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("request").user
        base_profile = user.profile
        if "profile" in validated_data:
            user_base_profile_data = validated_data.get("profile")
            save_base_profile_with_serializer(
                base_profile, user_base_profile_data,
                self.context.get("request")
            )
            validated_data.pop("profile")
        try:
            user_profile = CustomerService() \
                .create_customer(base_profile, validated_data)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return user_profile

    def update(self, instance, validated_data):
        user = self.context.get("request").user
        if instance.profile.user != user:
            raise PermissionDenied()

        if "profile" in validated_data:
            base_profile_data = validated_data.get("profile")
            save_base_profile_with_serializer(
                instance.profile, base_profile_data,
                self.context.get("request")
            )

            validated_data.pop("profile")

        updated_profile = super().update(instance, validated_data)
        return updated_profile

class CustomerProfileDetailSerializer(serializers.ModelSerializer):
    profile = BaseProfileListSerializer()
    profile_avatar = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()

    class Meta:
        model = CustomerModel
        fields = [
            "customer_id", 'website',
            "profile", "industry_name",
            "created_at", "is_active", "city",
            "country", "is_verified", "profile_avatar"
        ]

    def get_country(self, obj):
        return obj.get_country()

    def get_profile_avatar(self, obj):
        avatar = get_profile_avatar(profile=obj)
        if avatar is None:
            return None
        return AvatarDetailSerializer(avatar).data

class CustomerProfilePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerModel
        fields = [
            "customer_id", "profile",
            "industry_name", "website",
            "created_at", "is_verified"
        ]


