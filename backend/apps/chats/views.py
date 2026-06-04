"""
ViewSets for conversation and message API endpoints.

Handles all conversation-related operations:
- Creating conversations
- Listing user conversations
- Retrieving conversation details
- Sending messages
- Marking messages as read
"""

from django.db import transaction

from rest_framework import viewsets, status, generics, filters, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend


from .models import Conversation, Message, Negotiations
from .serializers import (
    ConversationSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageListSerializer,
    MessageCreateSerializer,
    NegotiationCreateSerializer,
    NegotiationDetailSerializer,
    NegotiationSerializer,
    NegotiationHistorySerializer,
    SupportRoomSerializer,
    MarkReadSerializer,
)
from .core.permissions import IsParticipant, NegotiationParticipantPermission, IsMessageSenderOrReadOnly
from .core.pagination import ConversationPagination, MessagePagination
from .services.support_service import (
    get_or_create_support_room,
    get_all_support_rooms,
    mark_messages_as_read,
)
from apps.core.utils.py import log_action, get_or_none
from apps.posts.services_T import return_paginated_view
import logging

logger = logging.getLogger(__name__)


class ConversationViewSet(
    mixins.ListModelMixin, 
    mixins.CreateModelMixin, 
    viewsets.GenericViewSet
    ):
    """
    ViewSet for managing conversations.

    Endpoints:
    - POST /api/conversations/ - Create new conversation
    - GET /api/conversations/ - List user's conversations
    - GET /api/conversations/{id}/ - Get conversation details
    """

    http_method_names = ["get", "post", 'patch']
    pagination_class = ConversationPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['-created_at']
    filterset_fields = {
        "participant_two__profile__display_name": ['icontains'],
        "participant_one__profile__display_name": ['icontains']
    }

    def get_permissions(self):
        if self.action in ("list", "retrieve", "patch"):
            return [IsParticipant()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """
        Use appropriate serializer based on action.

        - create: ConversationCreateSerializer (validation)
        - list: ConversationSerializer (summary)
        - retrieve: ConversationDetailSerializer (detailed)
        """
        if self.action == 'create':
            return ConversationCreateSerializer
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

    @transaction.atomic
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
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()

        log_action('conversation_created', request.user, {
            'conversation_id': conversation.pk,
            'participant_one': conversation.participant_one.id,
            'participant_two': conversation.participant_two.id
        })

        output_serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """
        List all conversations for current user.

        GET /api/conversations/

        Returns: Paginated list of conversations with message counts and unread status
        """
        return super().list(request, *args, **kwargs)

    @action(methods=["get", "post"], detail=True, url_path="messages")
    def retrieve_conversation(self, request, *args, **kwargs):
        """
        Retrieve detailed conversation information.

        GET /api/conversations/{id}/messages
        POST /api/conversations/{id}/messages
        """

        conversation = self.get_object()
        if not conversation.has_participant(request.user):
            if not (
                conversation.room_type == Conversation.RoomType.SUPPORT
                and request.user.is_staff
            ):
                raise PermissionDenied()
        
        if request.method == "GET":
            # mark all message as read
            mark_messages_as_read(conversation, request.user)

            serializer = ConversationDetailSerializer(conversation)
            return Response(serializer.data)
        else:
            serializer = MessageCreateSerializer(
                data=request.data,
                context={
                    'request': request,
                    'conversation': conversation
                }
            )
            serializer.is_valid(raise_exception=True)
            message = serializer.save()

            log_action('message_sent', request.user, {
                'message_id': message.pk,
                'conversation_id': conversation.pk
            })

            output_serializer = MessageSerializer(message)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

# Support Views

class OpenSupportRoomView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']
    def post(self, request, *args, **kwargs):
        
        if request.user.is_staff:
            raise PermissionDenied('Staff users cannot open a customer support room.')

        try:
            support_room = get_or_create_support_room(request.user)
            return Response(
                {
                    'room_id': str(support_room.conversation_id),
                    'ws_url': f'/ws/chat/{support_room.conversation_id}/'
                },
                status=status.HTTP_200_OK
            )
        except Exception as exc:
            return Response(status=400, data={"status": False, "details": str(exc)})

class SupportInboxView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = SupportRoomSerializer
    pagination_class = ConversationPagination

    def get_queryset(self):
        queryset = get_all_support_rooms()
        unread = self.request.query_params.get('unread')
        search = self.request.query_params.get('search')

        if unread and unread.lower() == 'true':
            queryset = queryset.filter(unread_count__gt=0)

        if search:
            queryset = queryset.filter(
                participant_one__is_staff=False, participant_two__profile__display_name=search
            )

        return queryset

class MarkMessagesReadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MarkReadSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room_id = serializer.validated_data['room_id']
        support_room = get_object_or_404(
            Conversation,
            conversation_id=room_id,
            room_type=Conversation.RoomType.SUPPORT
        )

        if not request.user.is_staff and not support_room.has_participant(request.user):
            raise PermissionDenied()

        updated_count = mark_messages_as_read(support_room, request.user)
        return Response({'marked_as_read': updated_count}, status=status.HTTP_200_OK)

class SupportRoomMessagesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id, *args, **kwargs):
        support_room = get_object_or_404(
            Conversation,
            conversation_id=room_id,
            room_type=Conversation.RoomType.SUPPORT
        )
        if not request.user.is_staff and not support_room.has_participant(request.user):
            raise PermissionDenied()

        limit = min(int(request.query_params.get('limit', 50)), 100)
        page = max(int(request.query_params.get('page', 1)), 1)
        offset = (page - 1) * limit

        queryset = Message.objects.filter(
            conversation=support_room,
            is_active=True
        ).select_related('sender').order_by('created_at')

        mark_messages_as_read(support_room, request.user)
        messages = list(queryset[offset:offset + limit])
        serializer = MessageListSerializer(messages, many=True)

        return Response(
            {
                'count': queryset.count(),
                'page': page,
                'limit': limit,
                'results': serializer.data,
            },
            status=status.HTTP_200_OK
        )

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages within conversations.
    """

    def get_serializer_class(self):

        if self.action in ("partial_update"):
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        """
        Get messages for conversation with optimizations.

        - select_related: Sender user object
        - Filter by conversation
        - Order by timestamp
        """
        conversation_id = self.kwargs.get('conversation_pk')

        queryset = Message.objects.filter(
            conversation_id=conversation_id
        ).select_related('sender').order_by('-created_at')

        return queryset

    http_method_names =  ["patch", "delete"]
    permission_classes = [IsMessageSenderOrReadOnly]
    
    def perform_destroy(self, instance):
        if isinstance(instance, Message):
            if hasattr(instance, "conversation"):
                if not instance.conversation.has_participant(self.request.user):
                    raise PermissionDenied()
                instance.soft_delete()
                log_action(
                    "deleted_message", self.request.user, {"message_id": instance.pk}
                )
        return Response(status=204)

class NegotiationViewSet(viewsets.ModelViewSet):
    permission_classes = [NegotiationParticipantPermission]
    http_method_names =  [
        "post", "get"
    ]

    def get_serializer_class(self):
        if self.action in ("create", "accept", "reject", "counter"):
            return  NegotiationCreateSerializer
        elif self.action == "retrieve":
            return NegotiationDetailSerializer
        elif self.action == "negotiation_history":
            return NegotiationHistorySerializer
        return NegotiationSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Negotiations.objects.filter(
            sender=user,
        ).select_related("conversation", "sender", "job_post")

        return queryset

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        negotiation = serializer.save()

        log_action(
            'negotiation_created', request.user, {
                "negotiation_id": negotiation.pk
            })

        response = NegotiationSerializer(negotiation)
        return  Response(response.data, status=status.HTTP_201_CREATED)

    def get_object(self):
        negotiation_pk = self.kwargs.get("pk", )

        if negotiation_pk is None:
            return Response({"status": "failed", "msg": "no_negotiation_pk"}, status=status.HTTP_400_BAD_REQUEST)

        user = self.request.user

        negotiation_obj = get_or_none(Negotiations, pk=negotiation_pk)
        if negotiation_obj is None:
            raise NotFound("negotiation instance not found")

        self.check_object_permissions(self.request, negotiation_obj)

        if negotiation_obj.conversation is not None:
            if not negotiation_obj.is_participants(user):
                raise PermissionDenied("You are not permitted to participate")
            return negotiation_obj
        elif negotiation_obj.job_post is  not None:
            if not negotiation_obj.is_participants(user):
                raise PermissionDenied("You are not permitted to participate")
            return negotiation_obj
        else:
            raise PermissionDenied()

    def update_status(self, request, status_act, *args, **kwargs):
        negotiation = self.get_object()
        serializer = self.get_serializer(negotiation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        log_action(
            action_type=status_act,
            user=request.user,
            details={
                "negotiation_id": instance.pk,
            }
        )
        response = NegotiationSerializer(instance)
        return Response(response.data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path="accept", detail=True)
    def accept(self, request, *args, **kwargs, ):
        return self.update_status(request, status_act='accept', *args, **kwargs)

    @action(methods=["post"], url_path="reject", detail=True)
    def reject(self, request, *args, **kwargs):
        return self.update_status(request, status_act='reject', *args, **kwargs)

    @action(methods=['post'], url_path="counter", detail=True)
    def counter(self, request, *args, **kwargs):
        return self.update_status(request, status_act='counter', *args, **kwargs)

    @action(methods=["get"], url_path='messages', detail=True)
    def negotiation_history(self, request, *args, **kwargs):
        negotiation = self.get_object()
        if not negotiation.is_participants():
            raise PermissionDenied()
        history = negotiation.histories.all()[:20]
        result = return_paginated_view(self, history)
        if "next" or "previous" not in result:
            serializer = self.get_serializer(history, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return result

