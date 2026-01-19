from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .serializers import Bookings, BookingCreateSerialzer
from .permissions import IsCustomer, IsCustomerOrProvider
from .helpers import _base_profile_by_pk

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import  method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction

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
        if self.action in ("create", "update", "destroy"):
            return [permissions.IsAuthenticated(), IsCustomer()]
        return [permissions.IsAuthenticated(), IsCustomerOrProvider()]
    
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup = self.kwargs.get("booking_pk")
        obj = get_object_or_404(queryset, pk=lookup)
        self.check_object_permissions(self.request, obj)
        return obj
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        base_profile_pk = self.kwargs.get("profile_pk")
        if base_profile_pk is None:
            return Response({"detail":"Profile 'pk' not found"},status=status.HTTP_400_BAD_REQUEST)
        base_profile = _base_profile_by_pk(base_profile_pk)
        provider_profile = base_profile.provider_profile if hasattr(base_profile, "provider_profile") else None
        if provider_profile is None:
            return Response({"detail": f"Provider profile not found for user {base_profile.user.email}"},status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data, context={"request": request, "provider": provider_profile})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, Bookings):
            instance.soft_delete()
            return Response({"detail": "Booking instance deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Failed to delete booking instance"}, exception=True,status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=["patch"], url_path="approve", detail=True)
    def approve_booking(self, request):
        pass

    @action(methods=["patch"], url_path="decline", detail=True)
    def decline_booking(self, request):
        pass
    
