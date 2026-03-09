"""
Serializers for conversation and message API endpoints.

Handles serialization and validation of conversation and message data.
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Conversation, Message
from apps.authentication.serializers import UserReadSerializer
from .core.utils import validate_message_content
from .services.conversations import ConversationService


from django.contrib.auth import get_user_model

import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for message data in API responses.

    Includes sender information and message metadata.
    """

    sender = User(read_only=True)
    sender_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender',
            'sender_id',
            'content',
            'is_read',
            'is_edited',
            'created_at',
            'edited_at',
        ]
        read_only_fields = [
            'id',
            'sender',
            'conversation',
            'is_edited',
            'edited_at',
            'created_at',
        ]

    def validate_content(self, value):
        """Validate message content."""
        is_valid, error_message = validate_message_content(value)
        if not is_valid:
            raise serializers.ValidationError(error_message)
        return value


class MessageListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing messages.

    Used for paginated message lists to reduce response size.
    Includes essential information without nested user objects.
    """

    sender_email = serializers.CharField(source='sender.email', read_only=True)
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'sender_email',
            'sender_name',
            'content',
            'is_read',
            'created_at',
        ]
        read_only_fields = fields

    def get_sender_name(self, obj):
        """Get sender's display name."""
        return obj.sender.full_name


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating messages.

    Validates message content and automatically associates with
    conversation and current user as sender.
    """

    class Meta:
        model = Message
        fields = ['content']

    def validate_content(self, value):
        """Validate message content."""
        is_valid, error_message = validate_message_content(value)
        if not is_valid:
            raise serializers.ValidationError(error_message)
        return value

    def create(self, validated_data):
        """
        Create message with conversation from context.

        Automatically sets sender as current user.
        """
        conversation = self.context.get('conversation')
        user = self.context.get('request').user

        if not conversation:
            raise serializers.ValidationError('Conversation not found.')

        if not conversation.has_participant(user):
            raise serializers.ValidationError(
                'You are not a participant of this conversation.'
            )

        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=validated_data['content']
        )

        logger.info(f"Message created: {message.pk} in conversation {conversation.pk}")
        return message


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for conversation data.

    Includes participant information, message count, and last message.
    """

    participant_one = UserReadSerializer(read_only=True)
    participant_two = UserReadSerializer(read_only=True)
    message_count = serializers.IntegerField(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'participant_one',
            'participant_two',
            'message_count',
            'last_message',
            'unread_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_last_message(self, obj):
        """Get last message in conversation."""
        last_message = obj.get_last_message()
        if last_message:
            return MessageListSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        """Get unread message count for current user."""
        user = self.context.get('request').user
        if user:
            return obj.messages.filter(
                is_read=False
            ).exclude(sender=user).count()
        return 0


class ConversationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for conversation information.

    Used when retrieving full conversation details with message preview.
    """

    participant_one = UserListSerializer(read_only=True)
    participant_two = UserListSerializer(read_only=True)
    message_count = serializers.IntegerField(read_only=True)
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'conversation_is',
            'participant_one',
            'participant_two',
            'message_count',
            'messages',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_messages(self, obj):
        """Get recent messages."""
        # Get last 10 messages (can be customized)
        messages = obj.messages.all()[:20]
        return MessageListSerializer(messages, many=True).data


class ConversationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating conversations.

    Validates participants and prevents duplicate conversations.
    """

    participant_two_id = serializers.IntegerField(write_only=True)
    participant_one = UserListSerializer(read_only=True)
    participant_two = UserListSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'participant_one',
            'participant_two',
            'participant_two_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'conversation_id',
            'participant_one',
            'participant_two',
            'created_at',
            'updated_at',
        ]

    def validate_participant_two_id(self, value):
        """Validate other participant exists."""

        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User not found.')

        return value

    def validate(self, data):
        """
        Validate conversation creation.

        - User cannot create conversation with themselves
        - Check for existing conversation
        """
        user = self.context['request'].user
        participant_two_id = data.get('participant_two_id')

        # Check for self-conversation
        if user.id == participant_two_id:
            raise serializers.ValidationError(
                'You cannot create a conversation with yourself.'
            )

        # Check for existing conversation
        existing = Conversation.objects.filter(
            models.Q(
                participant_one=user,
                participant_two_id=participant_two_id
            ) | models.Q(
                participant_one_id=participant_two_id,
                participant_two=user
            )
        ).exists()

        if existing:
            raise serializers.ValidationError(
                'A conversation already exists with this user.'
            )

        return data

    def create(self, validated_data):
        """Create conversation with current user as participant_one."""

        user = self.context['request'].user
        participant_two_id = validated_data.pop('participant_two_id')
        participant_two = User.objects.get(id=participant_two_id, is_active=True)

        try:
            service = ConversationService(
                participant_two=participant_two,
                participant_one=user
            )
            conversation = service.create_conversation(**validated_data)

        except Exception as e:
            logger.exception(f"exception: {str(e)}")
            raise ValidationError(str(e)

        return conversation


