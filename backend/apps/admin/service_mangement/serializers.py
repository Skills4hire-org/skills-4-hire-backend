from rest_framework import serializers
from ...users.services.models import ServiceCategory


class ServiceCategoryCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ServiceCategory
        fields = [
            "name", "description"
        ]

    