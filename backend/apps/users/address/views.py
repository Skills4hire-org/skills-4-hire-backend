
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from apps.core.exceptions import api_response, error_response
from .models import UserAddress
from .services.pagination import AddressPagination
from .services.permissions import IsAddressOwnerOrReadOnly

from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db import transaction
from django_filters.rest_framework import  DjangoFilterBackend

from .serializers import (
    AddressCreateSerializer, AddressDetailSerializer,
    AddressSerializer
)


class AddressViewSet(viewsets.ModelViewSet):

    http_method_names = ["post", 'get', 'patch', 'delete']
    filter_backends =  [DjangoFilterBackend]
    filterset_fields = ["state", "apartment", "street_address", "city", "country"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return AddressCreateSerializer
        elif self.action == "retrieve":
            return AddressDetailSerializer
        return AddressSerializer

    permission_classes = [IsAddressOwnerOrReadOnly]
    pagination_class = AddressPagination


    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False) or not getattr(user, "is_authenticated", False):
            return UserAddress.objects.none()

        profile = getattr(user, "profile", None)
        if profile is None:
            return UserAddress.objects.none()

        queryset = UserAddress.objects \
            .select_related("user_profile") \
            .filter(user_profile=profile) \
            .order_by('-created_at')

        return queryset

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        saved_address = serializer.save()
        output_serializer  = AddressSerializer(saved_address)

        return api_response(
            data=output_serializer.data,
            message="Address created successfully",
            status_code=status.HTTP_201_CREATED,
        )
