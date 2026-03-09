"""
ViewSets for conversation and message API endpoints.

Handles all conversation-related operations:
- Creating conversations
- Listing user conversations
- Retrieving conversation details
- Sending messages
- Marking messages as read
"""

from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.cache import cache_page

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageListSerializer,
    MessageCreateSerializer,
)
from .core.permissions import IsParticipant
from .core.pagination import ConversationPagination, MessagePagination
from core.utils import log_action
import logging

logger = logging.getLogger(__name__)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.

    Endpoints:
    - POST /api/conversations/ - Create new conversation
    - GET /api/conversations/ - List user's conversations
    - GET /api/conversations/{id}/ - Get conversation details
    - PATCH /api/conversations/{id}/mark-as-read/ - Mark all messages as read
    """

    http_method_names = ["get", "post", 'patch']
    permission_classes = [IsAuthenticated, IsParticipant]
    pagination_class = ConversationPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering = ['-updated_at']
    search_fields = [
        'participant_one__email', 'participant_two__email',
        "participant_one__username", "participant_two_username"
    ]

    def get_serializer_class(self):
        """
        Use appropriate serializer based on action.

        - create: ConversationCreateSerializer (validation)
        - list: ConversationSerializer (summary)
        - retrieve: ConversationDetailSerializer (detailed)
        """
        if self.action == 'create':
            return ConversationCreateSerializer
        elif self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationSerializer

    def get_queryset(self):
        """
        Get conversations for current user with optimizations.

        - select_related: Participant user objects
        - Filter by user participation
        - Order by most recent activity
        """
        user = self.request.user

        queryset = Conversation.objects.filter(
            Q(participant_one=user) | Q(participant_two=user)
        ).select_related(
            'participant_one',
            'participant_two'
        ).order_by('-updated_at')

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a new conversation.

        POST /api/conversations/

        Body:
        {
            "participant_two_id": 2
        }

        Returns: Conversation object with participants
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()

        log_action('conversation_created', request.user, {
            'conversation_id': conversation.id,
            'participant_one': conversation.participant_one.id,
            'participant_two': conversation.participant_two.id
        })

        output_serializer = ConversationSerializer(conversation)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


    def list(self, request, *args, **kwargs):
        """
        List all conversations for current user.

        GET /api/conversations/

        Returns: Paginated list of conversations with message counts and unread status
        """
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve detailed conversation information.

        GET /api/conversations/{id}/

        Returns: Conversation details with last 10 messages
        """
        conversation = self.get_object()
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark all messages in conversation as read.

        PATCH /api/conversations/{id}/mark-as-read/

        Returns: Updated conversation with unread_count = 0
        """
        conversation = self.get_object()

        # Mark all unread messages from other participant as read
        messages_to_update = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user)

        count = messages_to_update.update(is_read=True)

        log_action('messages_marked_read', request.user, {
            'conversation_id': conversation.id,
            'count': count
        })

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def unread_count(self, request, pk=None):
        """
        Get unread message count for conversation.

        GET /api/conversations/{id}/unread_count/

        Returns: {"unread_count": 5}
        """
        conversation = self.get_object()
        unread_count = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()

        return Response(
            {'unread_count': unread_count},
            status=status.HTTP_200_OK
        )


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages within conversations.

    Endpoints:
    - POST /api/conversations/{conversation_id}/messages/ - Send message
    - GET /api/conversations/{conversation_id}/messages/ - List messages (paginated)
    - PATCH /api/conversations/{conversation_id}/messages/{id}/ - Mark as read
    """

    permission_classes = [IsAuthenticated, IsParticipant]
    pagination_class = MessagePagination
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']  # Most recent first

    def get_serializer_class(self):
        """
        Use appropriate serializer based on action.

        - create: MessageCreateSerializer
        - list: MessageListSerializer (optimized)
        - retrieve/update: MessageSerializer (full)
        """
        if self.action == 'create':
            return MessageCreateSerializer
        elif self.action == 'list':
            return MessageListSerializer
        return MessageSerializer

    def get_queryset(self):
        """
        Get messages for conversation with optimizations.

        - select_related: Sender user object
        - Filter by conversation
        - Order by timestamp
        """
        conversation_id = self.kwargs.get('conversation_id')

        queryset = Message.objects.filter(
            conversation_id=conversation_id
        ).select_related('sender').order_by('-created_at')

        return queryset

    def get_conversation(self):
        """
        Get conversation object with permission check.

        Raises 404 if conversation doesn't exist or user is not participant.
        """
        conversation_id = self.kwargs.get('conversation_id')
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id
        )

        # Check if user is participant
        if not conversation.has_participant(self.request.user):
            raise PermissionError('You are not a participant of this conversation.')

        return conversation

    def create(self, request, conversation_id=None, *args, **kwargs):
        """
        Send a message to conversation.

        POST /api/conversations/{conversation_id}/messages/

        Body:
        {
            "content": "Hello, this is my message!"
        }

        Returns: Message object with full details
        """
        conversation = self.get_conversation()

        serializer = self.get_serializer(
            data=request.data,
            context={
                'request': request,
                'conversation': conversation
            }
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save()

        log_action('message_sent', request.user, {
            'message_id': message.id,
            'conversation_id': conversation.id
        })

        output_serializer = MessageSerializer(message)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, conversation_id=None, *args, **kwargs):
        """
        List messages in conversation (paginated).

        GET /api/conversations/{conversation_id}/messages/

        Query parameters:
        - page: Page number
        - page_size: Results per page (max 100)

        Returns: Paginated list of messages
        """
        conversation = self.get_conversation()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, conversation_id=None, pk=None, *args, **kwargs):
        """
        Get single message details.

        GET /api/conversations/{conversation_id}/messages/{id}/

        Returns: Message object
        """
        conversation = self.get_conversation()
        message = self.get_object()

        # Auto-mark as read when retrieved by recipient
        if message.sender != request.user and not message.is_read:
            message.mark_as_read()

        serializer = self.get_serializer(message)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, conversation_id=None, pk=None):
        """
        Mark single message as read.

        POST /api/conversations/{conversation_id}/messages/{id}/mark_as_read/

        Returns: Updated message object
        """
        conversation = self.get_conversation()
        message = self.get_object()

        # Only allow recipient to mark as read
        if message.sender == request.user:
            return Response(
                {'error': 'You cannot mark your own message as read'},
                status=status.HTTP_400_BAD_REQUEST
            )

        message.mark_as_read()

        log_action('message_read', request.user, {
            'message_id': message.id,
            'conversation_id': conversation.id
        })

        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConversationSearchView(generics.ListAPIView):
    """
    Search conversations by participant email or name.

    GET /api/conversations/search/?q=email@example.com

    Returns: List of matching conversations
    """

    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ConversationPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['participant_one__email', 'participant_two__email',
                     'participant_one__first_name', 'participant_two__first_name']

    def get_queryset(self):
        """Get user's conversations matching search."""
        user = self.request.user
        return Conversation.objects.filter(
            Q(participant_one=user) | Q(participant_two=user)
        ).select_related('participant_one', 'participant_two')