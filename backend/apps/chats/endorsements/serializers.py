from rest_framework import serializers

from ...authentication.serializers import UserReadSerializer
from ...users.serializers.profiles import ProviderProfilePublicSerializer
from .models import Endorsements

from rest_framework import serializers

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


class EndorsementDetailSerializer(serializers.ModelSerializer):
    endorsed_by = UserReadSerializer(read_only=True)
    provider = ProviderProfilePublicSerializer(read_only=True)
    class Meta:
        model = Endorsements
        fields = [
           'endorsement_id',  'endorsed_by', 'provider', 
            'message', 'extra_message', 'endorsed_at', 'is_active',
        ]
    