from rest_framework import viewsets
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from ..pagination import AdminPagination
from ..permissions import IsAdmin
from ..models import Support, SupportConversation
from .serializers import (
    SupportListSerializer, AssignAdminSerializer, SupportListConversationSerializer, 
    SupportConversationSerializer, ReplyMessageSerializer, SupportListMesssageSerialzer)
from ...core.exceptions import api_response, error_response
import logging

logger = logging.getLogger(__name__)

class SupportViewsets(viewsets.ModelViewSet):
    http_method_names = ['get', "patch"]
    pagination_class = AdminPagination
    permission_classes = [IsAdmin]
    serializer_class = SupportListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = [
        "is_active", "created_at", "assigned_at"
    ]
    search_fields = [
        "status", "customer__profile__display_name", 
        "customer__first_name", "sustomer__last_name"
    ]

    def get_serializer_class(self):
        if self.action == 'assign':
            return AssignAdminSerializer
        return SupportListSerializer

    def get_queryset(self):
        queryset = Support.objects.select_related(
            "customer", "admin"
            ).prefetch_related("conversations").order_by("-created_at")
        
        return queryset
    
    def partial_update(self, request, *args, **kwargs):
        return 
    
    @action(methods=['patch'], detail=True, url_path="assign")
    def assign(self, request, *args, **kwargs):
        try:
            support = self.get_object()
            serializer = self.get_serializer(support, data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return api_response(
                data=SupportListSerializer(instance).data,
                status_code=200
            )
        except Exception as error:
            logger.error("Failed to assign support: %s", error)
            return error_response(message='Internal Server Error', status_code=500)

    @action(methods=['patch'], detail=True, url_path=r"(?P<admin_action>[^/.]+)")
    def admin_action(self, request, *args, **kwargs):
        try:
            adm_action = kwargs.get("admin_action")
            actions = Support.Status.values
            if adm_action not in actions:
                return api_response(
                    data={}, message="Invalid Request", status_code=400
                )
            
            support: Support = self.get_object()

            if adm_action == Support.Status.CLOSED:
                support.closed_at = timezone.now()
                support.status = Support.Status.CLOSED

            elif adm_action == Support.Status.CRITICAL:
                support.status = Support.Status.CRITICAL

            elif adm_action == Support.Status.RESOLVED:
                support.resolved_at = timezone.now()
                support.status = Support.Status.RESOLVED

            else:
                return api_response(
                    data={}, message="Invalid Request", status_code=400
                )
            support.save()

            return api_response(
                data={ "status": True},
                message=f"Support has been reviewed and {adm_action}",
                status_code=200
            )
        except Exception as error:
            logger.error("Error performing admin action on support: %s", error)
            return error_response(message="Internal Server Error", status_code=500)

class ConversationViewsets(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', "post"]

    def get_serializer_class(self):
        if self.action == "list":
            return SupportListConversationSerializer
        if self.action == "reply":
            return ReplyMessageSerializer
        return SupportConversationSerializer
    
    def create(self, request, *args, **kwargs):
        return 
    
    def get_queryset(self):
        user = self.request.user
        queryset = None
        if user.is_staff:
            queryset = SupportConversation.objects.select_related(
                "support").prefetch_related(
                    "messages").all().order_by(
                        "-created_at")
        else:
            queryset = SupportConversation.objects.filter(
                support__customer=user).select_related(
                    "support").prefetch_related("messages").order_by("-created_at")
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        conversation: SupportConversation = self.get_object()

        conversation.messages.filter(
            is_read=False).exclude(
                sender=request.user).update(
                    is_read=True)

        return super().retrieve(request, *args, **kwargs)

    @action(methods=['post'], detail=True, url_path='reply')
    def reply(self, request, *args, **kwargs):
        try:
            conversation = self.get_object()
            serializer = self.get_serializer(data=request.data, context={'conversation': conversation, "request": request})
            serializer.is_valid(raise_exception=True)
            message_instance = serializer.save()

            return api_response(
                data=SupportListMesssageSerialzer(message_instance).data,
                status_code=201
            )
        except Exception as error:
            logger.error("Failed to reply to support conversation: %s", error)
            return error_response(message="Internal Server error", status_code=500)

            