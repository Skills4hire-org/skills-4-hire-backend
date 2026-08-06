from rest_framework import viewsets
from .models import UserAddress
from .services.pagination import AddressPagination
from .services.permissions import IsAddressOwnerOrReadOnly

from django_filters.rest_framework import  DjangoFilterBackend

from .serializers import (
    AddressCreateSerializer, AddressDetailSerializer
)

class AddressViewSet(viewsets.ModelViewSet):
    filter_backends =  [DjangoFilterBackend]
    filterset_fields = ["state", "apartment", "street_address", "city", "country"]
    permission_classes = [IsAddressOwnerOrReadOnly]
    pagination_class = AddressPagination

    def perform_create(self, serializer):
        serializer.save(user_profile=self.request.user.profile)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return AddressCreateSerializer
        return AddressDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False) or not getattr(user, "is_authenticated", False):
            return UserAddress.objects.none()
        
        queryset = UserAddress.objects \
            .select_related("user_profile") \
            .filter(user_profile=user.profile) \
            .order_by('-created_at')

        return queryset


