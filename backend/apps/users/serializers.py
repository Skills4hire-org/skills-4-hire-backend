from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.db import transaction, DatabaseError
from django.utils.translation import gettext_lazy as _

from .base_model import BaseProfile
from .provider_models import ProviderModel, Service,ServiceImage
from .customer_models import CustomerModel
from ..users.address.serializers import AddresSerializer
from .helpers import save_both_profiles, save_customer_profile, save_provider_profile, check_active_role, logger
from .profile_avater.serializers import AvaterSerializer

User = get_user_model()

def validate_request(request):
    if request is None:
        raise serializers.ValidationError("Authenticaction credentials are not provided")

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

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta: 
        model = CustomerModel
        fields = [
            "industry",
            "website",
            "total_hires",
            "country"
        ]
    
class OnboardingSerializer(serializers.Serializer):
    """Handles onboarding user roles"""
    CHOICES = ["SERVICE_PROVIDER", "CUSTOMER", "BOTH"]
    role = serializers.ChoiceField(choices=CHOICES, required=True, write_only=True)

    def validate(self, data):
        role = data.get("role", None)
        request = self.context.get("request", None)
        validate_request(request)
        if role.upper() not in self.CHOICES:
            raise serializers.ValidationError("Incorrect role provided %s", self.CHOICES)
        return data
    
    def save(self, **kwargs):
        request = self.context.get("request", None)
        role = self.validated_data.get("role", None)
        if role.upper() == self.CHOICES[0]:
            save_provider_profile(request)
        elif role.upper() == self.CHOICES[1]:
            save_customer_profile(request)
        elif role.upper() == self.CHOICES[2]:
            save_both_profiles(request)
        else:
            raise serializers.ValidationError("Invalid request")
        return self.validated_data

class BaseProfileUpdateSerializer(serializers.Serializer):

    gender = serializers.CharField(max_length=200, required=False)
    bio = serializers.CharField(max_length=1000, required=False)
    location = serializers.CharField(max_length=200, required=False)

    provider_profile = ProviderProfileSerializer(required=False)
    customer_profile = CustomerProfileSerializer(required=False)
    def validate_gender(self, value):
            allowed_gender = ["MALE", "FEMALE", "OTHER"]
            if value.upper() not in allowed_gender:
                raise   serializers.ValidationError(f"Only allowed gender is {allowed_gender}")
            return value
    def validate(self, data):
        request = self.context["request"]
        validate_request(request)
        if "provider_profile" in data and request.user.active_role != User.RoleChoces.SERVICE_PROVIDER:
            raise serializers.ValidationError("User is not a Provider")
        if "customer_profile" in data and request.user.active_role != User.RoleChoices.CUSTOMER:
            raise serializers.ValidationError("User is not a CUSTOMER")
        return data

    def create(self, instance, validated_data):
        gender =  validated_data.get("gender", None)
        bio = validated_data.get("bio", None)
        location = validated_data.get("location", None)

        provider_profile = validated_data.get("provider_profile", None)
        customer_profile = validated_data.get("customer_profile", None)
        request = self.context.get("request")
        if any([gender, bio, location]):
            base_profile = request.user.profile if hasattr(request.user, "profile") else None
            if base_profile:
                with transaction.atomic():
                    for field in ("gender", "bio", "location"):
                        setattr(base_profile, field, validated_data.get(field))
                    base_profile.save()
            raise serializers.ValidationError("Invalid request. Your account has no profile")
        if provider_profile:
            if request.user.active_role != User.RoleChoices.SERVICE_PROVIDER:
                raise serializers.ValidationError("User is not a provider")
            profile = request.user.profile.provider_profile if hasattr(request.user.profile, "provider_profile") else None
            if profile:
                with transaction.atomic():
                    for field, _ in provider_profile.items():
                        setattr(profile, field, validated_data.get("provider_profile")[field])
                    profile.save()
            raise serializers.ValidationError("Invalid request. Your account has no profile")
        if customer_profile:
            if request.user.active_role != User.RoleChoices.CUSTOMER:
                raise serializers.ValidationError("User is not a customer")
            profile = request.user.profile.customer_profile if hasattr(request.user.profile, "customer_profile") else None
            if profile:
                with transaction.atomic():
                    for field, _ in customer_profile.items():
                        setattr(profile, field, validated_data.get("customer_profile")[field])
                    profile.save()
            raise serializers.ValidationError("Invalid request. Your account has no profile")
        
        return instance

class BaseProfileReadSerializer(serializers.ModelSerializer):

    provider_profile = ProviderProfileSerializer(read_only=True)
    customer_profile = CustomerProfileSerializer(read_only=True)
    address = AddresSerializer(many=True, read_only=True)
    avater = AvaterSerializer(read_only=True)
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
            "customer_profile",
            "address",
            "avater"
        ]

    def get_active_role(self, obj):
        if not hasattr(obj, "user"):
            raise serializers.ValidationError("This user has no user object")

        return obj.user.active_role

class SwitchRoleSerializer(serializers.Serializer):
    """Handles switching user roles"""
    role = serializers.ChoiceField(choices=OnboardingSerializer.CHOICES, required=True, write_only=True)
    choices = ["service_provider", "customer"]
    def validate(self, data):
        request = self.context.get("request", None)
        validate_request(request)
        role = data.get("role", None)
        if role.lower() not in self.choices:
            raise serializers.ValidationError("Incorrect role provided %s", self.choices)
        if request.user.active_role == role.upper():
            raise serializers.ValidationError("User already has the role %s", role.upper())
        return data

    def save(self, **kwargs):
        request = self.context.get("request", None)
        role = self.validated_data.get("role", None)
        request.user.active_role = role.upper()
        request.user.save(update_fields=["active_role"])
        return request.user

class ServiceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceImage
        fields = [
            "image_url",
            "image_public_id"
        ]
    
class ServiceSerializer(serializers.ModelSerializer):
    images = ServiceImageSerializer(required=False)
    class Meta:
        model = Service
        fields = [
            "name",
            "description",
            "min_charge",
            "max_charge",
            "images",
            "is_active",
            "created_at"
        ]
        read_only_fields = ["created_at", "is_active"]
        
    default_error_messages = {
        "charge_empy": _("Charge cannot be empty")
    }
    def validate(self, attrs):
        validate_request(self.context.get("request"))
        min_charge = attrs["min_charge"] if hasattr(attrs, "min_charge") else None
        max_charge = attrs["max_charge"] if hasattr(attrs, "max_charge") else None
        if any([min_charge, max_charge]) is None:
            self.fail("charge_empty")
        if min_charge <= 0 or max_charge <= 0:
            raise serializers.ValidationError("Charge cannot be negetive")
        if min_charge >= max_charge:
            raise serializers.ValidationError("Min charge can not be greater than the max_cahrge")
        return attrs
    
    def create(self, validated_data):
        request = self.context.get("request")
        service_image = validated_data.get("images", None)
        if check_active_role(request) != User.RoleChoices.SERVICE_PROVIDER:
            raise serializers.ValidationError("User is not a provider")
        profile = request.user.profile.provider_profile if hasattr(request.user.profile, "provider_profile") else None
        if profile is None:
            raise serializers.ValidationError("Invalid Request, No profile object found for user %s", request.user.email)
        try:
            with transaction.atomic():
                service = Service.objects.create(profile=profile, **validated_data)
                if service_image:
                    images = [ServiceImage(service=service, **data) for data in service_image]
                    ServiceImage.objects.bulk_create(images)
        except DatabaseError:
            logger.exception("Failed  to populate database. service request failed on database operations", exc_info=True)
            raise
        except Exception:
            raise
            
        return validated_data
    
    @transaction.atomic
    def update(self, instance, validated_data):
        images = validated_data.get("images", None)
        request = self.context.get("request")
        if images is not None:
            if not hasattr(request.user.profile.provider_profile, "services"):
                raise serializers.ValidationError("User has no services to update")
            service = request.user.profile.provider_profile.services.images.filter(image_id=instance.images.image_id, is_active=True).first()
            for field, value in images.items():
                setattr(service, field, value)
            service.save()
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.min_charge = validated_data.get("min_charge", instance.min_charge)
        instance.max_charge = validated_data.gaet("max_cahrge", instance.max_cahrge)
        instance.save()
        return instance
