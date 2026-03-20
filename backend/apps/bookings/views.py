from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied


from .serializers import (Bookings, BookingCreateSerializer, BookingStatusUpdateSerializer,
                          BookingOutSerializer)
from .permissions import IsCustomer, IsCustomerOrProvider
from .helpers import provider_profile
from .paginations import CustomBookingPagination
from .services import BookingService
from apps.users.provider_models import ProviderModel

from django.db.models import Q
from django.utils.decorators import  method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

import logging

logger = logging.getLogger(__name__)

class BookingViewSet(viewsets.ModelViewSet):
    pagination_class = CustomBookingPagination

    def get_serializer_class(self):
        if self.action in ("list", "retrieve", "fetch_bookings"):
            return BookingOutSerializer
        return BookingCreateSerializer
    
    def get_queryset(self):
        """" A base queryset to fetch all booking associated to the request.user"""
        queryset = Bookings.objects.select_related(
                "customer", "provider__profile", "address")\
                .prefetch_related("service")\
                .filter(is_active=True, is_deleted=False).all()
        
        if getattr(self, "swagger_fake_view", False):
            return Bookings.objects.none()
        if queryset is None:
            return 1
        return queryset
        
    def get_permissions(self):
        if self.action in ("create", "update", "destroy"):
            return [permissions.IsAuthenticated(), IsCustomer()]
        return [IsCustomerOrProvider()]
    
    @method_decorator(transaction.atomic)
    def create(self, request, *args, **kwargs):
        provider_profile_id = self.kwargs.get("profile_pk")
        profile = provider_profile(provider_profile_id)
        serializer = self.get_serializer(data=request.data, context={"request": request, "provider": profile})
        if not serializer.is_valid(raise_exception=True):
            return Response({
                "status": "failed","errors": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.validated_data)
        return Response({"status": "success", "detail": serializer.data}, status=status.HTTP_201_CREATED, headers=headers)

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        status = request.query_params.get("status", None)

        provider_pk = kwargs.get("profile_pk")
        if request.user.is_superuser or request.user.is_staff:
            queryset = self.get_queryset().filter(provider__pk=provider_pk, 
                                                )
        else:
            queryset = self.get_queryset().filter(
                Q(provider__pk=provider_pk),
                Q(customer=request.user),
            )

        if queryset is None:
            return Bookings.objects.none
        
        if status is not None:
            status = status.upper()
            queryset = queryset.filter(booking_status__icontains=status)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response({
            "status": "success", 
            "detail": self.get_serializer(queryset, many=True).data},
            status=status.HTTP_200_OK)
    
    @method_decorator(transaction.atomic)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @method_decorator(transaction.atomic)
    def partial_update(self, request, *args, **kwargs):
        booking_instance = self.get_object()
        serializer = BookingStatusUpdateSerializer(booking_instance, 
                                                   data=request.data, 
                                                   context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                self.perform_update(serializer)
        except Exception:
            raise 
        return Response({"status": "success", "detail": f"Booking status updated to {booking_instance.booking_status}"}, status=status.HTTP_200_OK)
    
    
    @method_decorator(transaction.atomic)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, Bookings):
            BookingService.delete_booking(instance, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Failed to delete booking instance"}, exception=True,status=status.HTTP_400_BAD_REQUEST)

       
    @method_decorator(cache_page(60 * 10))
    @action(methods=["get"], detail=False)
    def fetch_bookings(self, request, *args, **kwargs):

        status = request.query_params.get("status")
        queryset = self.filter_queryset(self.get_queryset())
        if status is not None:
            status = status.upper()
            queryset = queryset.filter(booking_status__icontains=status)
        user = self.request.user
        if user.is_superuser or user.is_staff:
            paginate = self.paginate_queryset(queryset)
            return self.get_paginated_response(self.get_serializer(paginate, many=True).data)
        else:
            customer_provider_queryset = BookingService.customer_and_provider_view(user, queryset)
            paginate = self.paginate_queryset(customer_provider_queryset)
            return self.get_paginated_response(self.get_serializer(paginate, many=True).data)
    

        
