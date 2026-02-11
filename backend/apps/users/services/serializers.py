from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from ..provider_models import ServiceImage, Service
from ..serializers import validate_request
from ..helpers import check_active_role

from django.utils.translation import gettext_lazy as _
from django.db import transaction, DatabaseError
from django.contrib.auth import get_user_model

import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ServiceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceImage
        fields = [
            "image_url",
            "image_public_id",
            "is_active",
            "created_at",
        ]
    
class ServiceSerializer(serializers.ModelSerializer):
    images = ServiceImageSerializer(required=False, many=True)
    class Meta:
        model = Service
        fields = [
            "service_id",
            "name",
            "description",
            "min_charge",
            "max_charge",
            "images",
            "is_active",
            "created_at"
        ]
        read_only_fields = ["service_id", "created_at", "is_active"]
        
    default_error_messages = {
        "charge_empty": _("Charge cannot be empty")
    }
    def validate(self, attrs):
        validate_request(self.context.get("request"))
        min_charge = attrs.get("min_charge")
        max_charge = attrs.get("max_charge")

        if min_charge is None or max_charge is None:
            self.fail("charge_empty")
        if min_charge <= 0 or max_charge <= 0:
            raise serializers.ValidationError("Charge cannot be negetive")
        if min_charge >= max_charge:
            raise serializers.ValidationError("Min charge can not be greater than the max_cahrge")
        return attrs
    
    def create(self, validated_data):
        request = self.context.get("request")
        service_image = validated_data.pop("images")
        if check_active_role(request) != User.RoleChoices.SERVICE_PROVIDER:
            raise serializers.ValidationError("User is not a provider")
        profile = request.user.profile.provider_profile if hasattr(request.user.profile, "provider_profile") else None
        if profile is None:
            raise serializers.ValidationError("Invalid Request, No profile object found for user %s", request.user.email)
        try:
            with transaction.atomic():
                service = Service.objects.create(profile=profile, **validated_data)
                if service_image:
                    for items in service_image:
                        image = ServiceImage.objects.create(**items)
                        image.service.add(service)
        except DatabaseError:
            logger.exception("Failed  to populate database. service request failed on database operations", exc_info=True)
            raise DatabaseError("Failed to send save provider service")
        except Exception:
            raise serializers.ValidationError("Failed to save provider service!")
            
        return validated_data
    
    @transaction.atomic
    def update(self, instance, validated_data):
        images = validated_data.pop("images", None)
        request = self.context.get("request")
        user_profile = getattr(request.user.profile, "provider_profile")
        print(user_profile)
        print(instance.profile)
        if instance.profile != user_profile:
            raise PermissionDenied()
        with transaction.atomic():
            if images is not None:
                for item in images:
                    image_instances = ServiceImage.objects.filter(service=instance).update(**item)
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.save()

        return instance
