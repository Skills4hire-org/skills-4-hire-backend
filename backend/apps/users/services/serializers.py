from rest_framework import serializers
from .models import Service, ServiceAttachment, ServiceCategory, MainService
from ...core.utils.py import generate_thumbnails


class ServiceAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceAttachment
        fields = ["image_id", "image_url", "image_public_id", "type", "thumbnail_url", "created_at"]
        read_only_fields = ["image_id", "created_at", "thumbnail_url"]

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
    services = serializers.PrimaryKeyRelatedField(
        queryset=MainService.objects.all(), required=False, many=True
    )
    
    class Meta:
        model = Service
        fields = [
            "name", "description", "features",
            "services", "attachments",
            "years_of_experience",
            "charge", "is_default",
        ]

    def validate_charge(self, value: float):
        if value < 0:
            raise serializers.ValidationError("Value cannot be negative")
        return value

    def create(self, validated_data: dict) -> Service:
        attachments_data = validated_data.pop("attachments", [])
        services = validated_data.pop('services', [])
        user = self.context['request'].user
        if not user.is_provider:
            raise serializers.ValidationError("user is not a provider")
        profile = user.profile.provider_profile

        service = Service.objects.create(profile=profile, **validated_data)
        if services:
            service.services.set(services)
        if attachments_data:
            ServiceAttachment.objects.bulk_create(
                [
                    ServiceAttachment(
                        service=service,
                        thumbnail_url=generate_thumbnails(attachment.get('image_url', '')) if attachment.get('type', '').lower() == "video" else None,
                        **attachment
                    )
                    for attachment in attachments_data]
            )

        return service


    def update(self, instance: Service, validated_data: dict) -> Service:
        attachments_data = validated_data.pop("attachments", None)
        services = validated_data.pop("services", [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if services:
            instance.services.set(services)
        instance.save()
        if attachments_data is not None:
            # delete all existing attachments in a single query
            instance.attachments.delete()

            # Bulk-insert the fresh set
            ServiceAttachment.objects.bulk_create(
                [
                    ServiceAttachment(
                        service=instance,
                        thumbnail_url=generate_thumbnails(attachment.get('image_url', '')) if attachment.get('type', '').lower() == "video" else None,
                        **attachment
                    )
                    for attachment in attachments_data]
            )

        return instance
    
class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = [
            'name', 
            "service_category_id"
        ]

class MainServiceSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)
    class Meta:
        model = MainService
        fields  = [
            "main_service_id", "name", 
            "description", "category"
        ]

class ServiceListSerializer(serializers.ModelSerializer):
    attachments = ServiceAttachmentSerializer(many=True, read_only=True)
    services = MainServiceSerializer(read_only=True, many=True)
    
    class Meta:
        model = Service
        fields = [
            "service_id", "charge",
            "is_default", "years_of_experience",
            "is_active", "created_at", 
            "attachments", "services",
            "name", "description", "features"
        ]