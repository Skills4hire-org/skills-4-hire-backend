from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from ..users.serializers import validate_request, Service, ProviderProfileSerializer, BaseProfileReadSerializer
from ..users.services.serializers import ServiceSerializer
from ..users.base_model import Address
from ..users.address.serializers import AddresSerializer
from .models import Bookings
from .helpers import get_user_wallet, is_customer
from .services import _cancel_booking, _accept_booking
from ..authentication.serializers import UserReadSerializer

from decimal import Decimal
import logging


logger = logging.getLogger(__name__)

class BookingCreateSerialzer(serializers.ModelSerializer):
    address = AddresSerializer(required=True)
    service = ServiceSerializer(required=False)
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
        return attrs

    def validate_price(self, value):
        request = self.context.get("request")
        validate_request(self.context.get("request"))
        wallet = get_user_wallet(request=request)
        main_balance = getattr(wallet, "main_balance")
        if main_balance is None:
            raise serializers.ValidationError("User wallet has no balance")
        if Decimal(value) > Decimal(main_balance):
            raise serializers.ValidationError("Insufficient Balance. Top up to continue")
        return value
    
    def create(self, validated_data):
        address = validated_data.pop("address", None)
        service = validated_data.pop("service", None)
        provider = self.context.get("provider")
        request = self.context.get("request")
        if not is_customer(request):
            raise serializers.ValidationError("User is not a customer")
        
        with transaction.atomic():
            booking = Bookings.objects.create(customer=request.user, provider=provider, **validated_data)
            if address:
                add_obj, created = Address.objects.get_or_create(profile=getattr(request.user, "profile"),                                                                              postal_code=address.get("postal_code"))
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
            if service:
                services = []
                service_data = get_object_or_404(Service, name=service["name"].upper(), 
                                                profile=provider)
                booking.service.add(service_data)  
        return booking
    
    def update(self, instance, validated_data):
        address = validated_data.pop("address")
        service = validated_data.pop("service")
        if address:
            booking_address = getattr(instance, "address", None)
            if booking_address:
                with transaction.atomic():
                    address_obj = get_object_or_404(Address, pk=booking_address.pk, is_active=True, is_deleted=False)
                    for key, value in address.items():
                        if hasattr(booking_address, key):
                            setattr(address_obj, key, value)
                        address_obj.save()
                    instance.address = address_obj
                    instance.save()
            else:
                with transaction.atomic():
                    user_address = Address.objects.create(profile=instance.customer.profile, **address)
                    instance.address = user_address
                    instance.save()
        if service:
            services = []
            for data in service:
                service_data = get_object_or_404(Service, name=data["name"].title(), provider=instance.provider)
                services.append(service_data)
            instance.service.set(services)
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
        service_provider = getattr(instance.provider, "profile", None)
        if customer is None or service_provider is None:
            raise serializers.ValidationError(_("Invalid booking instance. Missing customer or provider information"))
        
        if instance.booking_status != Bookings.BookingStatus.PENDING:
            raise serializers.ValidationError(_("Only pending bookings can be updated"))
        
        if status.upper() == Bookings.BookingStatus.CANCELLED:
            if not _cancel_booking(instance, request.user):
                raise serializers.ValidationError(_("Failed to cancel booking"))
        elif status.upper() == Bookings.BookingStatus.COMPLETED:
            if request.user != getattr(service_provider, "user"):
                raise serializers.ValidationError(_("Only providers are able to accept bookings"))
            if not _accept_booking(instance, request.user):
                raise serializers.ValidationError(_("Error occurred while accepting booking"))
        else:
            raise serializers.ValidationError(_("Bad Request. Invalid request"))
        
        instance.booking_status = status.upper()
        instance.save()
        return instance

class BookingOutSerializer(serializers.ModelSerializer):
    customer = UserReadSerializer(read_only=True)
    provider = BaseProfileReadSerializer(source="provider.profile")
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


