from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Service
from .pagination import ServicePagination
from .permissions import IsOwnerOrReadOnly
from .serializers import ServiceSerializer


class ServiceViewSet(viewsets.ModelViewSet):

    http_method_names = ['post', 'get', 'patch', 'delete']

    serializer_class = ServiceSerializer
    pagination_class = ServicePagination
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]

    search_fields = ["name"]

    filterset_fields = {
        "is_active": ["exact"],
        "min_charge": ["gte", "lte"],
        "max_charge": ["gte", "lte"],
    }

    ordering_fields = ["min_charge", "max_charge", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Return only non-deleted services, with optimised joins.
        """
        return (
            Service.objects.filter(deleted_at__isnull=True)
            .select_related("profile")
            .prefetch_related("attachments")
            .order_by("-created_at")
        )

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance: Service = self.get_object()  # also runs object-level permission check
        instance.deleted_at = timezone.now()
        instance.is_active = False
        instance.save(update_fields=["deleted_at", "is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def auth_user_services(self, request, *args, **kwargs):
        user_profile = request.user.profile.provider_profile

        queryset = self.filter_queryset(self.get_queryset()).filter(profile=user_profile)
        if queryset is None:
            return Response({"empty": "no services "}, status=status.HTTP_200_OK)

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True).data
        return Response(serializer, status=status.HTTP_200_OK)
