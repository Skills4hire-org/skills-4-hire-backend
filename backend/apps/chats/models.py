"""
Models for conversations and messages.

Conversation: Represents a chat between exactly two users
Message: Represents individual messages within a conversation
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone

from apps.posts.models import Post

import logging
import uuid


logger = logging.getLogger(__name__)

class ActiveConversationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class Conversation(models.Model):
    """
    Model representing a conversation between exactly two users.

    Features:
    - Ensures only two participants
    - Prevents duplicate conversations between same users
    - Prevents self-conversations
    - Automatic timestamp tracking
    - Query optimization indexes
    """

    conversation_id = models.UUIDField(
        primary_key=True,
        unique=True,
        db_index=True,
        default=uuid.uuid4,
        help_text="pk  for conversation"
    )
    objects = models.Manager()
    active_objects = ActiveConversationManager()

    participant_one = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant_one',
        help_text='First participant in the conversation'
    )

    participant_two = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant_two',
        help_text='Second participant in the conversation'
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Status of this conversation"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Conversation creation timestamp'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last message timestamp (updates when new message added)'
    )

    class Meta:
        db_table = 'conversations_conversation'
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']

        # Ensure conversations are unique between two users (regardless of order)
        # This is a unique constraint on sorted participant IDs
        constraints = [
            models.UniqueConstraint(
                fields=['participant_one', 'participant_two'],
                name='unique_conversation_participants'
            ),
        ]

        # Indexes for fast participant lookups
        indexes = [
            models.Index(fields=['participant_one', 'participant_two']),
            models.Index(fields=['participant_two', 'participant_one']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(
                fields=['participant_one', 'updated_at'],
                name='conversation_user_updated_idx'
            ),
            models.Index(
                fields=['participant_two', 'updated_at'],
                name='conversation_user2_updated_idx'
            ),
        ]

    def __str__(self):
        """String representation of conversation."""
        return f"Conversation: {self.participant_one.email} <-> {self.participant_two.email}"

    def save(self, *args, **kwargs):
        """Validate conversation before saving."""
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validate conversation rules:
        - Users cannot chat with themselves
        - No duplicate conversations
        """
        # Check for self-conversation
        if self.participant_one == self.participant_two:
            raise ValidationError(
                'A user cannot create a conversation with themselves.'
            )

        # Check for duplicate conversations (considering both orders)
        if self.pk is None:  # Only check on creation, not update
            duplicate = Conversation.objects.filter(
                models.Q(
                    participant_one=self.participant_one,
                    participant_two=self.participant_two
                ) | models.Q(
                    participant_one=self.participant_two,
                    participant_two=self.participant_one
                )
            ).exists()

            if duplicate:
                raise ValidationError(
                    'A conversation already exists between these users.'
                )

    @property
    def other_participant(self, user):
        """
        Get the other participant in the conversation.

        Args:
            user: The user to find the other participant for

        Returns:
            User: The other participant
        """
        if user == self.participant_one:
            return self.participant_two
        elif user == self.participant_two:
            return self.participant_one
        return None

    def has_participant(self, user):
        """
        Check if user is a participant of this conversation.

        Args:
            user: User to check

        Returns:
            bool: True if user is a participant
        """
        return user == self.participant_one or user == self.participant_two

    @property
    def message_count(self):
        """Get total number of messages in conversation."""
        return self.messages.count()

    @property
    def unread_count(self, user):
        """
        Get number of unread messages for a user.

        Args:
            user: User to get unread count for

        Returns:
            int: Number of unread messages
        """
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def get_last_message(self):
        """
        Get the last message in conversation.

        Returns:
            Message: Last message or None
        """
        return self.messages.first()

class Message(models.Model):
    """
    Model representing a single message in a conversation.

    Features:
    - Must belong to a conversation
    - Tracks sender and read status
    - Automatic timestamp tracking
    - Indexed for efficient queries
    """

    objects = models.Manager()
    active_objects = ActiveConversationManager()

    message_id = models.UUIDField(
        primary_key=True,
        unique=True,
        db_index=True,
        default=uuid.uuid4,
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text='Conversation this message belongs to'
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text='User who sent this message'
    )

    content = models.TextField(
        max_length=5000,
        help_text='Message content'
    )

    is_read = models.BooleanField(
        default=False,
        help_text='Whether message has been read by recipient'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Message creation timestamp'
    )

    is_active = models.BooleanField(default=True)

    # Track edits
    is_edited = models.BooleanField(
        default=False,
        help_text='Whether message has been edited'
    )

    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp of last edit'
    )

    class Meta:
        db_table = 'conversations_message'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-created_at']  # Most recent first

        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['conversation', 'is_read']),
            models.Index(fields=['sender']),
            models.Index(fields=['created_at']),
            models.Index(
                fields=['conversation', 'is_read', 'created_at'],
                name='message_conv_read_created_idx'
            ),
        ]

    def __str__(self):
        """String representation of message."""
        preview = self.content[:50]
        return f"Message from {self.sender.email}: {preview}..."

    def save(self, *args, **kwargs):
        """Sanitize and save message."""
        # Validate sender is conversation participant
        if not self.conversation.has_participant(self.sender):
            raise ValidationError(
                'Message sender must be a participant of the conversation.'
            )

        # Update conversation's updated_at
        self.conversation.updated_at = self.created_at
        self.conversation.save(update_fields=['updated_at'])

        super().save(*args, **kwargs)

    def clean(self):
        """Validate message."""
        if not self.content or not self.content.strip():
            raise ValidationError('Message content cannot be empty.')

        if len(self.content) > 5000:
            raise ValidationError('Message exceeds maximum length of 5000 characters.')

        # Ensure sender is conversation participant
        if not self.conversation.has_participant(self.sender):
            raise ValidationError(
                'Message sender must be a participant of the conversation.'
            )

    def mark_as_read(self):
        """Mark message as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
            logger.debug(f"Message {self.message_id} marked as read")

    def mark_as_unread(self):
        """Mark message as unread."""
        if self.is_read:
            self.is_read = False
            self.save(update_fields=['is_read'])
            logger.debug(f"Message {self.message_id} marked as unread")

    def soft_delete(self):
        if self.is_actice:
            self.is_active = False
            self.save(update_fields=["is_active"])
            logger.debug(f"Message {self.message_id} deleted")

    def update_message_content(self):
        if hasattr(self, "is_edited"):
            setattr(self, "is_edited", True)
            setattr(self, "edited_at", timezone.now())
        self.save(update_fields=["is_edited", "edited_at"])

    @property
    def recipient(self):
        """Get the recipient of this message."""
        if self.sender == self.conversation.participant_one:
            return self.conversation.participant_two
        return self.conversation.participant_one

    @property
    def is_recent(self):
        """Check if message is from the last 24 hours."""
        from django.utils import timezone
        from datetime import timedelta

        time_threshold = timezone.now() - timedelta(hours=24)
        return self.created_at >= time_threshold


class Negotiations(models.Model):
    negotiation_id = models.UUIDField(
        max_length=20, primary_key=True,
        db_index=True, default=uuid.uuid4,
        editable=False
    )

    class Status(models.TextChoices):
        PROPOSED = 'PROPOSED'
        COUNTERED = "COUNTERED"
        ACCEPTED = "ACCEPTED"
        REJECTED = "REJECTED"

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE,
        related_name="negotiations", null=True, blank=True
    )
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="negotiations",db_index=True)

    status = models.CharField(choices=Status.choices, max_length=20, default=Status.PROPOSED)

    price =  models.DecimalField(decimal_places=2, max_digits=10, blank=False, null=False)

    final_price = models.DecimalField(decimal_places=2, max_digits=10, db_index=True, blank=True, null=True)

    job_post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name="negotiations",
        blank=True, null=True
    )
    note = models.TextField(blank=True, null=True)

    countered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "negotiation"
        db_table = "negotiationhistory"
        indexes = [
            models.Index(fields=["conversation"], name="conversation_idx"),
            models.Index(fields=["job_post"], name='job_post_idx'),
            models.Index(fields=['status'], name="nego_status_idx"),
            models.Index(fields=["countered_at"], name="countered_at_idx"),
            models.Index(fields=["accepted_at"], name="accepted_at_idx"),
            models.Index(fields=['price'], name="price_idx")
        ]



    def __str__(self):
        return f"Negotiation({self.negotiation_id}, {self.created_at}"


    def clean(self):
        if self.conversation:
            # Only people in this conversation can negotiate if conversation
            participants = (self.conversation.participant_one, self.conversation.participant_two)
            if self.sender not  in participants:
                raise ValidationError("You are not permitted to perform this action")

        if self.job_post:
            #Check is this is a valid job post
            if self.job_post.post_type != Post.PostType.JOB:
                raise ValidationError("This is not a valid job post that you can negotiate")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def is_accepted(self):
        if not hasattr(self, "accepted_at"):
            raise ValidationError("required field is not found")
        if self.accepted_at is not None:
            return True
        return False

    def is_participants(self, user) -> bool:
        if self.conversation is not None:
            participants = (self.conversation.participant_two,
                            self.conversation.participant_one,
                            self.sender
                        )

        elif self.job_post is not None:
            participants = (
                self.sender, self.job_post.user)
        else:
            participants = ()

        if user in participants:
            return True

        return False

    def set_final_price(self, price):
        if not hasattr(self, "final_price"):
            raise ValidationError("Final price field is not set")
        setattr(self, "final_price", price)
        self.save(update_fields=["final_price"])

    def reject(self):
        if not hasattr(self, "accepted_at"):
            return  False
        setattr(self, "rejected_at", timezone.now())
        self.save(update_fields=['rejected_at'])

    def accept(self):
        if not hasattr(self, "accepted_at"):
            return  False
        setattr(self, "accepted_at", timezone.now())
        self.save(update_fields=['accepted_at'])

    def counter(self):
        if not hasattr(self, "countered_at"):
            return  False
        setattr(self, "countered_at", timezone.now())
        self.save(update_fields=["countered_at"])

    def bulk_update(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                pass
        self.save()

    @property
    def receipient(self):
        if self.conversation is  not None:
            if self.sender == self.conversation.participant_one:
                return self.conversation.participant_two
            return self.conversation.participant_one
        elif self.job_post_id is not None:
            if self.sender == self.job_post.user:
                return self.sender
            return self.job_post.user
        return None

class NegotiationHistory(models.Model):
    history_id = models.UUIDField(
        primary_key=True, unique=True,
        default=uuid.uuid4, db_index=True
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
        related_name="negotiation_history")

    price = models.DecimalField(max_digits=10, decimal_places=2)

    negotiation = models.ForeignKey(
        Negotiations, on_delete=models.DO_NOTHING,
        related_name="histories"
    )
    action = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NegotiationHistory({self.history_id}"

    class Meta:
        db_table = "negotiation_history"
        indexes = [
            models.Index(fields=["action"], name="action_idx"),
            models.Index(fields=["negotiation"], name="nego_idx"),
            models.Index(fields=['created_at'], name="idx_date"),

        ]

    def clean(self):
        if self.action not in Negotiations.Status.values:
            raise ValidationError("Invalid Action")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


