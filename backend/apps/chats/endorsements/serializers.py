from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import Endorsements, ProviderModel
from ...core.utils.py import get_or_none
from .services import endorsement_already_exists, create_endorsement
from ...authentication.serializers import UserReadSerializer
from ...users.serializers.profiles import ProviderProfileDetailSerializer

class EndorsementCreateSerializer(serializers.ModelSerializer):

    provider_pk  = serializers.UUIDField(required=True, write_only=True)
    
    class Meta:
        model = Endorsements
        fields = [
            'provider_pk', 'reason', 'extra_message'
        ]

    def validate_reason(self, value):
        # clean str
        if len(value) > 500:
            raise serializers.ValidationError("Exceeded max length")
        return value.strip()

    def validate_extra_message(self, value):
        if len(value) > 200:
            raise serializers.ValidationError("Exceeded max length")
        return value.strip()
    
    def validate(self, data):
        user = self.context['request'].user
        if not user.is_customer:
            raise serializers.ValidationError("User is not a customer")
        
        if not self.instance:
            provider = get_or_none(ProviderModel, pk=data['provider_pk'], is_active=True)
            if provider is None:
                raise serializers.ValidationError("Profile not found")
            
            if endorsement_already_exists(customer_user=user, provider_user=provider):
                raise serializers.ValidationError("already endorsed this user")
        
            data['provider'] = provider
            data['endorsed_by'] = user

        return data

    def create(self, validated_data):
        validated_data.pop("provider_pk")
        endorsement = create_endorsement(
            **validated_data
        )
        return endorsement

    def update(self, instance, validated_data):

        endorsement = super().update(instance, validated_data)
        return endorsement
    
class EndorsementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endorsements
        fields = [
            'endorsed_by', 'provider', 'endorsement_id',
            'reason', 'extra_message', 'endorsed_at', 'is_active',
            'is_hidden'
        ]

class EndorsementDetailSerializer(serializers.ModelSerializer):
    endorsed_by = UserReadSerializer(read_only=True)
    provider = ProviderProfileDetailSerializer(read_only=True)
    class Meta:
        model = Endorsements
        fields = [
            'endorsed_by', 'provider', 'endorsement_id',
            'reason', 'extra_message', 'endorsed_at', 'is_active',
            'is_hidden'
        ]
    