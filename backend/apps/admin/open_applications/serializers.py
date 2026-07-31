from rest_framework import serializers

from .models import ApplicationCategory, OpenApplications

class ApplicationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationCategory
        fields = [
            "category_id", "name", "description"
        ]
        read_only_fields = [
            "category_id"
        ]

    def validate_name(self, value: str):
        return value.title()
    

class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta: 
        model = OpenApplications
        fields = '__all__'
        read_only_fields = [
            "application_id", "created_at", "updated_at"
        ]

class ApplicationListSerializer(ApplicationCreateSerializer):
    category = ApplicationCategorySerializer(read_only=True)

    class Meta(ApplicationCreateSerializer.Meta): 
        model = ApplicationCreateSerializer.Meta.model
        fields = ApplicationCreateSerializer.Meta.fields

        