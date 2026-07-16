from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model

from ..models import Support, SupportConversation, SupportMessage
from ...authentication.serializers import UserReadSerializer

UserModel = get_user_model()

class OpenTicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = SupportMessage
        fields = [
            "message", "features"
        ]

    def create(self, validated_data: dict):
        user = self.context['request'].user
        if user.is_staff:
            raise serializers.ValidationError("Tickets cannot be opened by staff members", code="staff-cannot-open-ticket")
        try:
            support = Support.objects.create(customer=user)
            conversation = SupportConversation.objects.create(support=support)
            validated_data.update({"conversation": conversation, "sender": user})

            super().create(validated_data=validated_data)
        except Exception as error:
            raise serializers.ValidationError(error)
        return conversation

class SupportListMesssageSerialzer(serializers.ModelSerializer):
    sender = UserReadSerializer(read_only=True)
    class Meta:
        model = SupportMessage
        fields = [
            "message_id", "sender", "is_staff", 
            "features", "message", "is_read", 
            "created_at", "updated_at"
        ]

class SupportConversationSerializer(serializers.ModelSerializer):
    messages = SupportListMesssageSerialzer(read_only=True, many=True)
    class Meta:
        model = SupportConversation
        fields = [
            'conversation_id', "created_at", "messages"
        ]
    
class SupportListConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    class Meta:
        model = SupportConversation
        fields = [
            "conversation_id", "created_at", "last_message"
        ]
    def get_last_message(self, obj: SupportConversation):
        message = obj.messages.last()
        return SupportListMesssageSerialzer(message).data
    
class SupportListSerializer(serializers.ModelSerializer):
    customer = UserReadSerializer(read_only=True)
    class Meta: 
        model = Support
        fields  = [
            "support_id", "status", 
            "customer", "is_active", "created_at", 
            "assigned_at",
            "updated_at", "resolved_at", "closed_at"
        ]

class AssignAdminSerializer(serializers.ModelSerializer):
    admin_id = serializers.UUIDField(write_only=True, required=True)
    class Meta:
        model = Support
        fields  = ["admin_id"]

    def validate_admin_id(self, value):
        user = UserModel.objects.get(pk=value)
        if not user.is_staff:
            raise serializers.ValidationError("User is not a staff user")
        return user
    
    def update(self, instance, validated_data: dict):
        admin = validated_data.pop("admin_id")
        validated_data.update({"assigned_at": timezone.now(), "admin": admin})
        return super().update(instance, validated_data)

class ReplyMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMessage
        fields = [
            "message", "features", "is_staff"
        ]

    def create(self, validated_data: dict):
        convesation: SupportConversation = self.context.get("conversation")
        user = self.context['request'].user

        if validated_data['is_staff']:
            support_room_admin = convesation.support.admin
            if user != support_room_admin:
                raise serializers.ValidationError("You are not the one assign to this room")

        validated_data.update({"conversation": convesation, "sender": user})
        result = super().create(validated_data=validated_data)
        return result