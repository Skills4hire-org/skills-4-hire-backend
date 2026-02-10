from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from ..users.serializers import  ServiceSerializer, validate_request, Service, ProviderProfileSerializer
from ..users.base_model import Address
from ..users.address.serializers import AddresSerializer
from .models import Bookings
from .helpers import get_user_wallet, is_customer
from .services import _cancel_booking, _accept_booking

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
                for data in service:
                    service_data = get_object_or_404(Service, name=[value["name"].upper() for value in data.values()], 
                                                 profile=provider)
                    services.append(service_data)
                booking.service.set(services)  
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
        if value.upper() is not self.choices:
            raise serializers.ValidationError("Bad Request. status is not in active choices")
        return value
    
    def update(self, instance, validated_data):
        status = validated_data.get("status", instance.status)
        request = self.context.get("request")
        booking_instance = self.context.get("booking")
        if booking_instance:
            if request.user not in (getattr(booking_instance, "customer"), getattr(booking_instance.provider.profile, "user")):
                raise PermissionDenied("You dont have access to perform this action")
            if booking_instance.booking_status != Bookings.BookingStatus.PENDING:
                raise serializers.ValidationError("Bad Request. You can only update pending bookings")
        if status.upper() == Bookings.BookingStatus.CANCELLED:
            if not _cancel_booking(booking_instance, request.user):
                raise serializers.ValidationError("Failed to cancel booking")
        elif status.upper() == Bookings.BookingStatus.COMPLETED:
            if request.user != getattr(booking_instance.provider.profile, "user"):
                raise serializers.ValidationError("Only providers are able to accept bookings")
            if not _accept_booking(booking_instance, request.user):
                raise serializers.ValidationError("Error occurred while accepting booking")
        else:
            raise serializers.ValidationError("Bad Request. Invalid request")
        
        return instance

class BookingOutSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source="customer.email", read_only=True)
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


