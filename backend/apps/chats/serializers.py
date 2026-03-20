"""
Serializers for conversation and message API endpoints.

Handles serialization and validation of conversation and message data.
"""
from django.db import models, transaction

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Conversation, Message, Negotiations, Post, NegotiationHistory
from apps.authentication.serializers import UserReadSerializer
from apps.core.utils.py import get_or_none
from .core.utils import (
    validate_message_content,
    validate_negotiation_notes, validate_negotiation_price,
    validate_status, log_history, sanitize_message_content,
    trigger_notification
)
from apps.posts.serializers import PostListSerializer
from .services.conversations import (
    ConversationService, NegotiationService,
)

from django.contrib.auth import get_user_model

import logging


User = get_user_model()
logger = logging.getLogger(__name__)


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for message data in API responses.

    Includes sender information and message metadata.
    """

    sender = UserReadSerializer(read_only=True)
    sender_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Message
        fields = [
            'message_id',
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
            'message_id',
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
            'message_id',
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
        value = sanitize_message_content(value)

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

    def update(self, instance: Message, validated_data: dict):

        print("serializer context", self.context)
        user = self.context.get("request").user

        message_content = validated_data["content"]

        if not instance.conversation.has_participant(user):
            raise serializers.PermissionDenied()

        if message_content is None:
            instance.content = None

        instance.content = message_content
        instance.update_message_content()
        instance.save(update_fields=["content"])

        return instance

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
        user = self.context.get("request").user
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

    participant_one = UserReadSerializer(read_only=True)
    participant_two = UserReadSerializer(read_only=True)
    message_count = serializers.IntegerField(read_only=True)
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
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
        # Get last 20 messages
        messages = obj.messages.all()[:20]
        return MessageListSerializer(messages, many=True).data


class ConversationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating conversations.

    Validates participants and prevents duplicate conversations.
    """

    participant_two_id = serializers.UUIDField(write_only=True, required=True)
    participant_one = UserReadSerializer(read_only=True)
    participant_two = UserReadSerializer(read_only=True)

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
            User.objects.get(pk=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError('User not found.')

        return value

    def validate(self, data):
        """
        Validate conversation creation.

        - User cannot create conversation with themselves
        - Check for existing conversation
        """
        user = self.context.get("request").user
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
                'A conversation already exists betweeen users.'
            )

        return data

    def create(self, validated_data):
        """Create conversation with current user as participant_one."""

        user = self.context['request'].user
        participant_two_id = validated_data.pop('participant_two_id')
        participant_two = User.objects.get(pk=participant_two_id, is_active=True)

        try:
            service = ConversationService(
                participant_two=participant_two,
                participant_one=user
            )
            conversation = service.create_conversation(**validated_data)

        except Exception as e:
            logger.exception(f"exception: {str(e)}")
            raise ValidationError(str(e))

        return conversation

class NegotiationCreateSerializer(serializers.ModelSerializer):

    sender = serializers.CharField(source="sender.email", read_only=True, required=False)
    conversation_id = serializers.UUIDField(write_only=True, required=False)
    job_post_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Negotiations
        fields = [
            "negotiation_id",
            "conversation_id",
            "job_post_id",
            "sender",
            "price",
            "status",
            "note",
        ]
        read_only_fields = [
            "negotiation_id",
            "sender",

        ]

    def validate_status(self, value):
        valid, message = validate_status(value)
        if not valid:
            raise serializers.ValidationError(message)
        return  value.strip()

    def validate(self, data):
        user = self.context.get("request").user

        if "conversation_id" in data:
            conversation_id = data["conversation_id"]
            conversation = get_or_none(Conversation, is_active=True, pk=conversation_id)
            if conversation is None:
                raise serializers.ValidationError("conversation obj not found")
            if not conversation.has_participant(user):
                raise serializers.ValidationError("You are not in this conversation")

        if "job_post_id" in data:
            job_post_id = data["job_post_id"]
            post = get_or_none(Post, is_ative=True, pk=job_post_id)
            if post is None:
                raise serializers.ValidationError("Post obj not Found")
            participants = (post.user, user)
            if user not in participants:
                raise serializers.ValidationError("you are not allowed to perform this action")
            if post is None:
                raise serializers.NotFound("post_not_found")
            if post.post_type != Post.PostType.JOB.value:
                raise serializers.ValidationError("Not a valid job post")

        return  data

    def validated_note(self, value):
        is_valid, message = validate_negotiation_notes(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        return value

    def validate_price(self, value):
        is_valid, message = validate_negotiation_price(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        return value

    def create(self, validated_data):
        user = self.context.get("request").user

        if not "conversation_id" in validated_data and not "job_post_id" in validated_data:
            raise serializers.ValidationError("Both conversation and job_post cannot be empty at the same time: There must be something to negotiate about")

        if "conversation_id" in validated_data:
            conversation_id = validated_data.pop("conversation_id")
            conversation = get_or_none(Conversation, is_active=True, pk=conversation_id)
            negotiation = NegotiationService(conversation=conversation, sender=user)
            create_negotiation = negotiation.create_negotiation(**validated_data)

        if "job_post_id" in validated_data:
            job_post_id = validated_data.pop("job_post_id")
            job_post = get_or_none(Post, is_active=True, pk=job_post_id)
            negotiation = NegotiationService(post=job_post, sender=user)
            create_negotiation = negotiation.create_negotiation(**validated_data)

        if "status" in validated_data:
            status = validated_data.get("status", "")
        else:
            status = create_negotiation.status
        log_history(negotiation=create_negotiation, sender=user,
                    price=validated_data["price"], action=status)

        return  create_negotiation

    def update(self, instance: Negotiations, validated_data):
        logger.debug(f"instance: {instance}, validated_data: {validated_data}")
        action = validated_data["status"]

        user = self.context.get("request").user

        if instance.status == Negotiations.Status.ACCEPTED:
            raise serializers.ValidationError("Negotiation already accepted and closed")
        elif instance.status == Negotiations.Status.REJECTED:
            raise serializers.ValidationError("Negotiation already rejected and closed")

        # prepare notification
        notification_type = action
        sender = user
        receiver = instance.receipient

        match action:
            case Negotiations.Status.ACCEPTED:
                with transaction.atomic():
                    accept = NegotiationService().accept_negotiation(instance, user=user)
                    if accept:
                        instance.set_final_price(validated_data["price"])
                        trigger_notification(notification_type, sender, receiver)
                        log_history(negotiation=instance, sender=user, action=action, price=validated_data["price"])
            case Negotiations.Status.REJECTED:
                with transaction.atomic():
                    reject = NegotiationService().reject_negotiation(instance, user=user)
                    if reject:
                        trigger_notification(notification_type, sender, receiver)
                        log_history(negotiation=instance, sender=user,
                                    price=validated_data["price"], action=action)
            case Negotiations.Status.COUNTERED:
                with transaction.atomic():
                    counter = NegotiationService().counter_negotiation(instance, user=user)
                    if counter:
                        trigger_notification(notification_type, sender, receiver)
                        log_history(negotiation=instance, sender=user,
                                    price=validated_data['price'], action=action)
        instance.bulk_update(validated_data)
        return instance

class NegotiationSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source="sender.user_id")
    conversation_id = serializers.SerializerMethodField()
    job_post_id = serializers.SerializerMethodField()

    class Meta:
        model = Negotiations
        fields = [
            "negotiation_id",
            "price",
            "note",
            "sender",
            "status",
            "conversation_id",
            "job_post_id",
            "countered_at",
            "created_at"
        ]

    def get_conversation_id(self, obj):
        if obj.conversation is not None:
            return obj.conversation.pk
        else:
            return None

    def get_job_post_id(self, obj):
        if obj.job_post is not None:
            return obj.job_post.pk
        else:
            return None

class NegotiationDetailSerializer(serializers.ModelSerializer):
    sender = UserReadSerializer(read_only=True)
    conversation = ConversationSerializer(read_only=True)
    job_post = PostListSerializer(read_only=True)
    class Meta:
        model = Negotiations
        fields = [
            "negotiation_id",
            "price",
            "note",
            "sender",
            "status",
            "conversation",
            "job_post",
            "accepted_at",
            "created_at",
            "countered_at"
        ]

class NegotiationHistorySerializer(serializers.ModelSerializer):
    sender_email = serializers.CharField(source="sender.email")
    negotiation_status = serializers.CharField(source='negotiation.status')

    class Meta:
        model = NegotiationHistory
        fields = [
            "history_id",
            "sender_email",
            "negotiation_status",
            "price",
            "action",
            "created_at"
        ]