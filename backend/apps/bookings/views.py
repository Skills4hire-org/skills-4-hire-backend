
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from .models import PaymentRequestBooking, BookingTransaction
from .serializers import (Bookings, BookingCreateSerializer,
                          BookingSerializer, AcceptRejectSerializer,
                          BookingDetailSerializer, PaymentRequestSerializer,
                          RequestSerializer, ReviewPaymentRequestSerializer, 
                          PaymentRequestDetailSerializer, RequestSerializer,
                          BookingTransactionSerializer
)

from .permissions import IsCustomer, IsBookingParticipants, IsProvider, IsRequestReceiverOrSender
from .paginations import CustomBookingPagination, CustomPaymentRequestPagination
from .services import BookingService
from .booking_transaction import transaction_ready_exists


from django.db.models import Q
from django.utils.decorators import  method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

import logging

logger = logging.getLogger(__name__)

class BookingViewSet(viewsets.ModelViewSet):
    pagination_class = CustomBookingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "booking_status": ['icontains']
    }

    http_method_names = ['post', 'get', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return BookingCreateSerializer
        if self.action == 'accept_or_reject':
            return AcceptRejectSerializer
        if self.action == 'retrieve':
            return BookingDetailSerializer
        if self.action == 'request_payout':
            return PaymentRequestSerializer
        return BookingSerializer

    @action(methods=['patch'], detail=True, url_path='accept_or_reject')
    def accept_or_reject(self, request, *args, **kwargs):

        booking = self.get_object()
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "booking": booking})
        
        serializer.is_valid(raise_exception=True)

        idempotency = serializer.validated_data['idempotency_key']
        user = request.user

        if transaction_ready_exists(user, idempotency=idempotency)[0]:

            return Response(
                status=status.HTTP_409_CONFLICT,
                data={
                    "status": "success",
                    'msg': "Found duplicate transaction",
                    'data': BookingTransactionSerializer(transaction_ready_exists(user, idempotency)[1]).data
                }
            )

        saved_booking = serializer.save()
        output_serializer = BookingSerializer(saved_booking).data
        return Response(output_serializer, status=status.HTTP_200_OK)

    def get_queryset(self):
        """" A base queryset to fetch all booking associated to the request.user"""
        if getattr(self, "swagger_fake_view", False):
            return Bookings.objects.none()
        
        user = self.request.user
        queryset =  (
            Bookings.objects.select_related(
                "customer", 'provider', 'address', 'cancelled_by', 'accepted_by'
                ).prefetch_related("attachments")
        )   
        if user.is_customer:
            queryset = queryset.filter(customer=user)
        else:
            queryset = queryset.filter(provider=user.profile.provider_profile)

        return queryset

    def get_permissions(self):
        if self.action in ("create", "partial_update", "destroy"):
            return [IsCustomer()]
        if self.action == 'request_payout':
            return [IsProvider()]
        return [IsBookingParticipants()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        idempotency = serializer.validated_data['idempotency_key']
        user = request.user

        if transaction_ready_exists(user, idempotency=idempotency)[0]:
    
            logger.info("Dublicate Booking Found, returning the initial request")

            return Response(
                status=status.HTTP_200_OK,
                data={
                    "status": "success",
                    'msg': "Duplicate Booking, Returning initial transaction",
                    "data": BookingTransactionSerializer(transaction_ready_exists(user, idempotency)[1]).data
                }
            )
        
        created_booking = serializer.save()
        output_serializer = BookingSerializer(created_booking).data
        return Response(output_serializer, status=status.HTTP_201_CREATED)


    @method_decorator(cache_page(60 * 2))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    
    @method_decorator(transaction.atomic)
    def partial_update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @method_decorator(transaction.atomic)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, Bookings):
            BookingService().delete_booking(instance, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Failed to delete booking instance"}, exception=True,status=status.HTTP_400_BAD_REQUEST)

        
    @action(methods=['post'], detail=True, url_path='request_payout')
    def request_payout(self, request, *args, **kwargs):
        booking = self.get_object()
        serializer = self.get_serializer(data=request.data, 
                                         context={'request': request, "booking": booking})
        serializer.is_valid(raise_exception=True)
        output_serializer = serializer.save()
        return Response(RequestSerializer(output_serializer).data, status=status.HTTP_201_CREATED)
    

class BookingPaymentRequestViewSet(RetrieveModelMixin, viewsets.GenericViewSet):

    pagination_class = CustomPaymentRequestPagination
    def get_permissions(self):
        if self.action == 'payment_request_review':
            return [IsCustomer()]
        return [IsRequestReceiverOrSender()]

    def get_serializer_class(self):
        if self.action == 'payment_request_review':
            return ReviewPaymentRequestSerializer
        if self.action == 'retrieve':
            return PaymentRequestDetailSerializer
        return RequestSerializer

    def get_queryset(self):
        user = self.request.user
        queryset =PaymentRequestBooking.objects.select_related("booking", "customer", 'provider')\
            .prefetch_related("attachments_payment_request")
        
        if user.is_customer:
            queryset = queryset.filter(customer=user)
        elif user.is_provider:
            queryset = queryset.filter(provider=user.profile.provider_profile)
    
        return queryset

    http_method_names = ['post', "get"]

    @action(methods=['post'], detail=True, url_path='review')
    def payment_request_review(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={'request': request, "payment_request": self.get_object()})
        serializer.is_valid(raise_exception=True)

        idempotency = serializer.validated_data['idempotency_key']

        user = request.user

        if transaction_ready_exists(user, idempotency=idempotency)[0]:
            logger.info("Dublicate Transaction Found, returning the initial request")

            return Response(
                status=status.HTTP_200_OK,
                data={
                    "status": "success",
                    'msg': "Duplicate Transaction, Returning initial transaction",
                    "data": BookingTransactionSerializer(transaction_ready_exists(user, idempotency)[1]).data
                }
            )

        output_serializer = serializer.save()
        return Response(RequestSerializer(output_serializer).data, status=status.HTTP_200_OK)
