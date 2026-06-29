from rest_framework import serializers
from .models import Service, ServiceAttachment, ServiceCategory


class ServiceAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceAttachment
        fields = ["image_id", "image_url", "image_public_id", "created_at"]
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
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(), required=True
    )
    
    class Meta:
        model = Service
        fields = [
            "category_id", "attachments",
            "name",  "years_of_experience",
            "description", "charge", "is_default",
        ]

    def validate_name(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("name must not be empty.")
        return value.strip().title()  # Normalize to title case for consistency

    def validate_charge(self, value: float):
        if value < 0:
            raise serializers.ValidationError("Value cannot be negative")
        return value

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

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if attachments_data is not None:
            #delete all existing attachments in a single query
            instance.attachments.delete()

            # Bulk-insert the fresh set
            ServiceAttachment.objects.bulk_create(
                [ServiceAttachment(service=instance, **attachment) for attachment in attachments_data]
            )

        return instance
    
class ServiceCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceCategory
        fields = [
            'name',
            "service_category_id"
        ]

class ServiceListSerializer(serializers.ModelSerializer):
    attachments = ServiceAttachmentSerializer(many=True, read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    
    class Meta:
        model = Service
        fields = [
            "service_id",
            "name", "description", "charge",
            "is_default", "years_of_experience",
            "is_active", "created_at", 
            "attachments", "category"
        ]