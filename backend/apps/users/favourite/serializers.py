from rest_framework import serializers

from .models import Favourite, ProviderModel
from ...core.utils.py import get_or_none
from ..serializers.profiles import ProviderProfilePublicSerializer


import uuid

class FavouriteAddSerializer(serializers.ModelSerializer):

    provider_id = serializers.UUIDField(required=True, write_only=True)

    class Meta:
        model = Favourite
        fields = [
            "provider_id"
        ]

    def validate(self, data):

        provider_id = data['provider_id']
        provider = get_or_none(ProviderModel, pk=str(provider_id))
    
        if provider is None:
            raise serializers.ValidationError("Provider profile  not found")
        
        data['provider'] = provider
        return data
    
    def create(self, validated_data):
        current_user = self.context['request'].user
        try:
            favourite, created = Favourite.objects.get_or_create(owner=current_user)
            
            provider = validated_data['provider']
            if favourite.providers.filter(provider_id=provider.provider_id).exists():
                raise serializers.ValidationError("You have add this profile into your list of favourite")
            
            favourite.providers.add(provider)

        except Exception as exc:
            raise serializers.ValidationError(str(exc))
        
        return validated_data

    def update(self, instance: Favourite, validated_data):
        try:
            provider = validated_data['provider']
            print(validated_data)
            instance.providers.remove(provider)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))
        return instance
    

class FavouriteListSerialzer(serializers.ModelSerializer):
    providers = ProviderProfilePublicSerializer(many=True, read_only=True)
    class Meta:
        model = Favourite
        fields = [
            "favourite_id", 'created_at', 
            'providers', "updated_at"
        ]
