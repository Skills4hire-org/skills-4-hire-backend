from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from .serializers import Bookings, BookingCreateSerialzer
from .permissions import IsCustomer, IsCustomerOrProvider
from .helpers import _base_profile_by_pk

from django.db.models import Q

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingCreateSerialzer
    queryset  = Bookings.objects.select_related("customer", "provider__profile", "service")

    def get_queryset(self):
        """" A base queryset to fetch all booking associated to the request.user"""
        qs = self.queryset.filter(is_active=True, is_deleted=False).all()
        if qs is None:
            return self.queryset.none()
        return qs.filter(Q(customer=self.request.user), Q(provider=self.request.user.profile.provider_profile))
    
    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsCustomer()]
        return [permissions.IsAuthenticated(), IsCustomerOrProvider()]
    
    def create(self, request, *args, **kwargs):
        base_profile_pk = self.kwargs.get("profile_pk")
        if base_profile_pk is None:
            return Response("Profile 'pk' not found",status=status.HTTP_400_BAD_REQUEST)
        base_profile = _base_profile_by_pk(base_profile_pk.strip())
        provider_profile = base_profile.provider_profile if hasattr(base_profile, "provider_profile") else None
        if provider_profile is None:
            return Response(f"Provider profile not found for user {base_profile.user.full_name}",status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data, context={"request": request, "provider": provider_profile})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
