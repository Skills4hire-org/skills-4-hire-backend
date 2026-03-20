from rest_framework import serializers

from django.utils.text import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from ..customer_models import CustomerModel
from ..profile_services.customer_profile import CustomerService
from ..profile_services.provider_profile import ProviderProfileServices
from ..profile_services.utils import already_has_a_profile
from ..provider_models import ProviderModel

VALID_CHOICES = ["CUSTOMER", "SERVICE_PROVIDER"]

class OnboardingSerializer(serializers.Serializer):
    service_to_perform = serializers.CharField(write_only=True) # customer or provider

    def validate_service_to_perform(self, value):
        if value.upper() not in VALID_CHOICES:
            raise serializers.ValidationError(_(f"Invalid role: {VALID_CHOICES}"))
        return value.strip()

    def create(self, validated_data):
        user = self.context.get("request").user

        if already_has_a_profile(user):
            raise serializers.ValidationError("profile already exists")

        service = validated_data.get("service_to_perform", "")
        if service  is None:
            raise serializers.ValidationError("role to play is required")


        user_profile = None # either customer profile or provider profile
        if service.upper() == VALID_CHOICES[0]:
            # customer user/client
            if CustomerModel.objects.filter(profile=user.profile).exists():
                raise ValidationError("profile already exists")
            user_profile = CustomerService().create_customer(user.profile)

        elif service.upper() == VALID_CHOICES[1]:
            # skilled professional
            if ProviderModel.objects.filter(profile=user.profile).exists():
                raise ValidationError("profile already exists")
            user_profile = ProviderProfileServices().create_provider_profile(user.profile)
        else:
            raise serializers.ValidationError(_("Invalid service"))

        return user_profile








