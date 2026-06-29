from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import Service, ServiceCategory
from .pagination import ServicePagination
from .permissions import IsOwnerOrReadOnly, IsServiceProvider
from .serializers import ServiceCreateSerializer, ServiceListSerializer, ServiceCategorySerializer
from ...posts.services_T import return_paginated_view
from ...core.exceptions import api_response, error_response

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    queryset = ServiceCategory.objects.all().only("name", "service_category_id").order_by("name")
    serializer_class = ServiceCategorySerializer
    pagination_class = None  # Disable pagination for categories
    permission_classes = [IsAuthenticated]

class ServiceViewSet(viewsets.ModelViewSet):

    http_method_names = ['post', 'get', 'patch', 'delete']
    pagination_class = ServicePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]

    search_fields = ["@name", "@category__name"]
    filterset_fields = {
        "name": ["icontains"],
        "is_active": ["exact"],
        "charge": ["gte", "lte"],
        "category__name": ["icontains"],
    }

    def get_permissions(self):
        if  self.action in ("create", "auth_user_services"):
            return [IsServiceProvider()]
        if  self.action in ("partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return ServiceCreateSerializer

        return ServiceListSerializer
    
    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    
    def get_queryset(self):
        """
        Return only non-deleted services, with optimised joins.
        """
        return (
            Service.objects.filter(is_active=True, deleted_at__isnull=True)
            .select_related("profile", "category")
            .prefetch_related("attachments")
        )

    def destroy(self, request, *args, **kwargs) -> Response:
        instance: Service = self.get_object()  # also runs object-level permission check
        instance.deleted_at = timezone.now()
        instance.is_active = False
        instance.save(update_fields=["deleted_at", "is_active", "updated_at"])
        return api_response(status_code=status.HTTP_204_NO_CONTENT)

    @method_decorator(cache_page(60 * 5))
    @action(methods=['get'], detail=False)
    def auth_user_services(self, request, *args, **kwargs):
        try:
            user_profile = request.user.profile.provider_profile
        except Exception as e:
            return error_response(message=str(e), errors=e)
        queryset = self.filter_queryset(self.get_queryset()).filter(profile=user_profile)
        if queryset is None:
            return api_response(data={}, message="success")

        return return_paginated_view(self, queryset)
    