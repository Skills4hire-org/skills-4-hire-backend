from rest_framework import serializers

from ...authentication.serializers import UserReadSerializer
from ...users.serializers.profiles import ProviderProfilePublicSerializer
from .models import Endorsements
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

def has_endorsed(provider, user):
    return user.endorsed_by.filter(provider=provider, is_active=True).exists()

class EndorsementCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Endorsements
        fields = [
            'provider', 'message', 'extra_message'
        ]
        extra_kwargs = {
            'provider': {
                'error_messages': {
                    'does_not_exist': 'The selected provider user does not exist.'
                }
            }
        }
    def validate_provider(self, value):
        user = self.context['request'].user
        if has_endorsed(value, user):
            raise serializers.ValidationError(_("You have already endorsed this profile"))
        return value

class EndorsementDetailSerializer(serializers.ModelSerializer):
    endorsed_by = UserReadSerializer(read_only=True)
    provider = ProviderProfilePublicSerializer(read_only=True)

    class Meta:
        model = Endorsements
        fields = [
           'endorsement_id',  'endorsed_by', 'provider', 
            'message', 'extra_message', 'endorsed_at', 'is_active',
        ]
    