from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from ..users.serializers import (
    validate_request, 
    Service, 
    ProviderProfileSerializer, 
    BaseProfileReadSerializer
)
from ..users.services.serializers import ServiceSerializer
from ..users.base_model import Address
from ..users.address.serializers import AddresSerializer
from .models import Bookings
from .helpers import is_customer
from .services import BookingService
from ..authentication.serializers import UserReadSerializer
from apps.wallet.services import WalletService

from decimal import Decimal
import logging


logger = logging.getLogger(__name__)

class BookingCreateSerialzer(serializers.ModelSerializer):
    address = AddresSerializer(required=True)
    service = ServiceSerializer(required=False, many=True)
    class Meta:
        model = Bookings
        fields = [
            "address",
            "service",
            "price",
            "notes",
            "descriptions",
            "start_date",
            "end_date",
            "currency",
            "payment_remark"
        ]
    def validate(self, attrs):
        validate_request(self.context.get("request"))
        if attrs.get("start_date") or attrs.get("end_date"):
            if attrs["start_date"] >= attrs["end_date"]:
                raise serializers.ValidationError("'end_date' cannot be greater that the 'start_date'")
            elif attrs["start_date"].date() < timezone.now().date():
                raise serializers.ValidationError("invalid start date. can't be less than today")
        return attrs

    def validate_price(self, value):
        request = self.context.get("request")
        validate_request(self.context.get("request"))

        wallet = WalletService.get_user_wallet(user=request.user)

        main_balance = getattr(wallet, "main_balance")
        
        if main_balance is None:
            raise serializers.ValidationError("User wallet has no balance")
        if Decimal(value) > Decimal(main_balance):
            raise serializers.ValidationError("Insufficient Balance. Top up to continue")
        return value
    
    def create(self, validated_data):
        address = validated_data.pop("address", None)
        services = validated_data.pop("service", None)
        provider = self.context.get("provider")
        request = self.context.get("request")
        if not is_customer(request):
            raise serializers.ValidationError("User is not a customer")
        
        with transaction.atomic():
            booking = Bookings.objects.create(customer=request.user, provider=provider, **validated_data)
            if address:
                add_obj, created = Address.objects.get_or_create(profile=getattr(request.user, "profile"),                                                                            postal_code=address.get("postal_code"))
                if created:
                    for key, value in address.items():
                        if hasattr(add_obj, key):
                            setattr(add_obj, key, value)
                    add_obj.save()
                    booking.address = add_obj
                    booking.save()
                else:
                    booking.address = add_obj
                    booking.save()
            if services:
                service_names = [
                    s["name"]
                    for s in services
                ]
                available_services = Service.objects.filter(
                    name__in=service_names,
                    profile=provider
                )
                
                booking.service.set(available_services) 
        return booking
    
    @transaction.atomic
    def update(self, instance: Bookings, validated_data):
        address = validated_data.pop("address", None)
        service = validated_data.pop("service", None)
        if address:
            booking_address = instance.address
            if booking_address:
                address_instance = Address.objects.get(
                                        profile=instance.customer.profile,
                                        pk=booking_address.pk,
                                        is_active=True)
                for key, value in address.items():
                    setattr(address_instance, key, value)
                address_instance.save()
                booking_address = address_instance
                booking_address.save()
            else:
                new_address = Address.objects.create(profile=instance.customer.profile, **address)
                instance.address = new_address
                instance.save()
        if service:
            service_names = [
                s["name"] 
                for s in service
            ]
            if instance.service.filter(name__in=service_names):
                updated_services = Service.objects.filter(name__in=service_names, profile=instance.provider)
                instance.service.set(updated_services)
            else :
                new_services = Service.objects.filter(name__in=service_names, profile=instance.provider)
                instance.service.set(new_services)

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
            
class BookingStatusUpdateSerializer(serializers.Serializer):
    choices = getattr(Bookings.BookingStatus, "values")
    status = serializers.ChoiceField(choices=choices)

    def validate_status(self, value):
        validate_request(self.context.get("request"))
        if value.upper() not in self.choices:
            raise serializers.ValidationError("Bad Request. status is not in active choices")
        return value
    
    def update(self, instance, validated_data):
        status = validated_data.get("status", instance.booking_status)
        request = self.context.get("request")
        if not isinstance(instance, Bookings):
            raise serializers.ValidationError(_("Instance is not of type Bookings"))
        
        customer = getattr(instance, "customer", None)
        service_provider = instance.provider
        if customer is None or service_provider is None:
            raise serializers.ValidationError(_("Invalid booking instance. Missing customer or provider information"))
        
        if instance.booking_status != Bookings.BookingStatus.PENDING:
            raise serializers.ValidationError(_("Only pending bookings can be updated"))
        
        if status.upper() == Bookings.BookingStatus.CANCELLED:
            if not BookingService.cancel_booking(instance, request.user):
                raise serializers.ValidationError(_("Failed to cancel booking"))
        elif status.upper() == Bookings.BookingStatus.COMPLETED:
            if request.user != getattr(service_provider.profile, "user"):
                raise PermissionDenied()
            if not BookingService.accept_booking(instance, request.user):
                raise serializers.ValidationError(_("Error occurred while accepting booking"))
        else:
            raise serializers.ValidationError(_("Bad Request. Invalid request"))
        
        instance.booking_status = status.upper()
        instance.save()
        return instance

class BookingOutSerializer(serializers.ModelSerializer):
    customer = UserReadSerializer(read_only=True)
    provider = ProviderProfileSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    address = AddresSerializer(read_only=True)
    class Meta:
        model = Bookings
        fields = [
            "booking_id",
            "booking_status",
            "customer",
            "provider",
            "service",
            "address",
            'currency',
            "price",
            "notes",
            "descriptions",
            "payment_remark",
            "is_active",
            "start_date",
            "end_date",
            "created_at",
            "cancelled_at"
        ]


