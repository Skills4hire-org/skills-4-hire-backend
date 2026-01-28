from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action


from .serializers import (Bookings, BookingCreateSerialzer, BookingStatusUpdateSerializer,
                        BookingOutSerializer)
from .permissions import IsCustomer, IsCustomerOrProvider
from .helpers import _base_profile_by_pk
from .paginations import CustomBookingPagination
from ..users.base_model import BaseProfile

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import  method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

import logging

logger = logging.getLogger(__name__)

class BookingViewSet(viewsets.ModelViewSet):
    queryset  = Bookings.objects.select_related("customer", "provider__profile", "address").prefetch_related("service")
    pagination_class = CustomBookingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["booking_status"]
    #serializer_class = BookingOutSerializer
    
    def get_serializer_class(self):
        if self.request.method == "get":
            return BookingOutSerializer
        return BookingCreateSerialzer
    
    def get_queryset(self):
        """" A base queryset to fetch all booking associated to the request.user"""
        qs = self.queryset.filter(is_active=True, is_deleted=False).all()
        if qs is None:
            return self.queryset.none()
        try:
            provider_profile = getattr(self.request.user.profile, "provider_profile")
            qs = qs.filter(Q(customer=self.request.user) | Q(provider=provider_profile))
        except BaseProfile.provider_profile.RelatedObjectDoesNotExist:
            qs = qs.filter(customer=self.request.user)

        return qs

    def get_permissions(self):
        if self.action in ("create", "update", "destroy"):
            return [permissions.IsAuthenticated(), IsCustomer()]
        return [permissions.IsAuthenticated(), IsCustomerOrProvider()]
    
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup = self.kwargs.get("pk")
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
    
    @action(methods=["patch"], detail=True)
    def booking_status_update(self, request, pk=None):
        booking_instance = self.get_object()
        serializer = BookingStatusUpdateSerializer(data=request.data, context={"request": request, "booking": booking_instance})
        serializer.is_valid(raise_exception=True)
        status = serializer.validated_data.get("status")
        try:
            self.perform_create(serializer)
        except Exception:
            raise 
        return Response({"status": "success", "detail": f"Booking instance {status}"}, status=status.HTTP_200_OK)
    
    @method_decorator(cache_page(60 * 15))
    @action(methods=["get"], detail=False)
    def fetch_bookings(self, request):
        logger.debug("Found view")
        status = request.query_params.get("status")
        qs = self.filter_queryset(self.get_queryset())
        if status is None:
            qs = qs.none()
        else:
            qs = qs.filter(booking_status__iexact=status.upper())
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response({"status": "success", "detail": serializer.data}, status=status.HTTP_200_OK)



        
