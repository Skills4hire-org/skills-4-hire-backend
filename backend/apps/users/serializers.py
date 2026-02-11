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
            "provider_id",
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
        if "provider_profile" in data and request.user.active_role != User.RoleChoices.SERVICE_PROVIDER:
            raise serializers.ValidationError("User is not a Provider")
        if "customer_profile" in data and request.user.active_role != User.RoleChoices.CUSTOMER:
            raise serializers.ValidationError("User is not a CUSTOMER")
        return data

    def update(self, instance, validated_data):
        gender =  validated_data.get("gender", None)
        bio = validated_data.get("bio", None)
        location = validated_data.get("location", None)

        provider_profile = validated_data.get("provider_profile", None)
        customer_profile = validated_data.get("customer_profile", None)
        request = self.context.get("request")
        if any([gender, bio, location]):
            base_profile = getattr(request.user, "profile", None)
            if base_profile is not None:
                with transaction.atomic():
                    for field in ("gender", "bio", "location"):
                        setattr(base_profile, field, validated_data.get(field).title())
                    base_profile.save()
            else:
                raise serializers.ValidationError("Invalid request. Your account has no profile")
        if provider_profile:
            if request.user.active_role != User.RoleChoices.SERVICE_PROVIDER:
                raise serializers.ValidationError("User is not a provider")
            
            profile = getattr(request.user.profile, "provider_profile", None)
            if profile is not None:
                print("found")
                with transaction.atomic():
                    for field, value in provider_profile.items():
                        setattr(profile, field, value)
                    profile.save()
            else:
                with transaction.atomic():
                    provider_profile = save_provider_profile(request=request)
                    for field, value in provider_profile.items():
                        setattr(provider_profile, field, value)
                    provider_profile.save()
                
        if customer_profile is not None:
            if request.user.active_role != User.RoleChoices.CUSTOMER:
                raise serializers.ValidationError("User is not a customer")
            profile = getattr(request.user.profile, "customer_profile")
            if profile is not None:
                with transaction.atomic():
                    for field, value in customer_profile.items():
                        setattr(profile, field, value)
                    profile.save()
            else:
                with transaction.atomic():
                    custom_profile = save_customer_profile(request=request)
                    for field, value in customer_profile.items():
                        setattr(custom_profile, field, value)
                    custom_profile.save()
            
        return validated_data

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