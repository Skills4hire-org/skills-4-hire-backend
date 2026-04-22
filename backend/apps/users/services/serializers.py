from rest_framework import serializers
from .models import Service, ServiceAttachment, ServiceCategory
from ..serializers.profiles import ProviderProfilePublicSerializer


class ServiceAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceAttachment
        fields = ["image_id", "image_url", "image_public_id", "is_active", "created_at"]
        read_only_fields = ["image_id", "created_at"]

    def validate_image_url(self, value: str) -> str:
        """
        URLField already validates format; this guard ensures the value is
        non-empty and explicitly rejects accidental blank submissions.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("image_url must not be blank.")
        return value

    def validate_image_public_id(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("image_public_id must not be empty.")
        return value.strip()

class ServiceCreateSerializer(serializers.ModelSerializer):
    attachments = ServiceAttachmentSerializer(many=True, required=False)
    category_id = serializers.UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = Service
        fields = [
            "category_id",
            "attachments",
            "name", 
            "description",
            "min_charge",
            "max_charge",
            "is_default",
        ]

    def validate_category_id(self, value):
        # validate the category id and return the category instance if present else None
        if value is None:
            return None
        try:
            category = ServiceCategory.objects.get(category_id=value)
            return category
        except ServiceCategory.DoesNotExist:
            raise serializers.ValidationError("Invalid category_id provided.")
        
    def validate_name(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("name must not be empty.")
        return value.strip().title()  # Normalize to title case for consistency

    def validate(self, attrs: dict) -> dict:
        min_charge = attrs["min_charge"]
        max_charge = attrs["max_charge"]

        if min_charge > max_charge:
            raise serializers.ValidationError(
                {"min_charge": "min_charge must be less than or equal to max_charge."}
            )

        return attrs


    def create(self, validated_data: dict) -> Service:
        attachments_data = validated_data.pop("attachments", [])
        category = validated_data.pop("category_id", None)

        validated_data["category"] = category
        user = self.context['request'].user
        if not user.is_provider:
            raise serializers.ValidationError("user is not a provider")
        profile = user.profile.provider_profile

        service = Service.objects.create(profile=profile, **validated_data)

        if attachments_data:
            ServiceAttachment.objects.bulk_create(
                [ServiceAttachment(service=service, **attachment) for attachment in attachments_data]
            )

        return service


    def update(self, instance: Service, validated_data: dict) -> Service:
        attachments_data = validated_data.pop("attachments", None)
        category = validated_data.pop("category_id", None)
        if category is not None:
            validated_data["category"] = category

        # Update scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if attachments_data is not None:
            # Soft-deactivate all existing attachments in a single query
            instance.attachments.filter(is_active=True).update(is_active=False)

            # Bulk-insert the fresh set
            ServiceAttachment.objects.bulk_create(
                [ServiceAttachment(service=instance, **attachment) for attachment in attachments_data]
            )

        return instance
    
class ServiceCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceCategory
        fields = [
            'name', "description", 'created_at',
            "service_category_id"
        ]

class ServiceListSerializer(serializers.ModelSerializer):
    attachments = ServiceAttachmentSerializer(many=True, read_only=True)
    profile = ProviderProfilePublicSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    
    class Meta:
        model = Service
        fields = [
            "service_id", "profile",
            "name", "description",
            "min_charge", "max_charge",
            "is_default", "is_verified",
            "is_active", "created_at", 
            "attachments", "category"
        ]