from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import NotificationReadSerializer, Notification
from .paginations import NotificationPagination
from .permissions import IsNotificationOwnerOrAdmin

from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction

class NotificationViewSet(viewsets.ModelViewSet):

    queryset = (
        Notification.objects.filter(is_deleted=False)\
            .order_by("-created_at")\
            .select_related("user")
    )
    serializer_class = NotificationReadSerializer
    pagination_class = NotificationPagination
    permission_classes = [permissions.IsAuthenticated, IsNotificationOwnerOrAdmin]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["event", "content", "is_read"]

    http_method_names = ["get", "delete", "post"]

    def get_queryset(self):
        user = self.request.user

        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        
        qs = self.queryset
        if user.is_superuser or user.is_staff:
            return qs
        else:
           return qs.filter(user=user)

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @method_decorator(transaction.atomic)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def perform_destroy(self, instance):
        if isinstance(instance, Notification):
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return False
    
    @method_decorator(transaction.atomic)
    @action(methods=["post"], detail=True, url_path="mark-read")
    def mark_read(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, Notification):
            instance.mark_as_read()
            return Response({
                "status": "success", "detail": f"Notification instance {instance.pk} is marked as read"},
                status=status.HTTP_200_OK)
        



    


