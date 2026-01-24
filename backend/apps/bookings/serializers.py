from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from ..users.serializers import AddresSerializer, ServiceSerializer, validate_request, Address, Service
from .models import Bookings
from .helpers import get_user_wallet, is_customer
from .services import _cancel_booking, _accept_booking

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
        if attrs["start_date"] >= attrs["end_date"]:
            raise serializers.ValidationError("'end_date' cannot be greater that the 'start_date'")
        
    def validate_price(self, value):
        request = self.context.get("request")
        wallet = get_user_wallet(request=request)
        main_balance = getattr(wallet, "main_balance")
        if main_balance is None:
            raise serializers.ValidationError("User wallet has no balance")
        if round(int(value, 2)) > main_balance:
            raise serializers.ValidationError("Insufficient Balance. Top up to continue")
        return value
    
    def create(self, validated_data):
        address = validated_data.get("adress")
        service = validated_data.get("service")
        provider = self.context.get("provider")
        request = self.context.get(request)
        if not is_customer(request):
            raise serializers.ValidationError("User is not a customer")
        try:
            with transaction.atomic():
                booking = Bookings.objects.create(
                    customer=request.user, 
                    provider=provider,
                    price=validated_data.get("price"),
                    notes=validated_data.get("notes"),
                    descriptions=validated_data.get("descriptions"),
                    start_date=validated_data.get("start_date"),
                    end_date=validated_data.get("end_date"),
                    currency=validated_data.get("currency"),
                    payment_remark=validated_data.get("payment_remark")
                    )
                if address:
                    address, created = Address.objects.get_or_create(**address)
                    booking.address = address
                if service:
                    services = []
                    for data in service:
                        service_data = get_object_or_404(Service, name=data["name"], profile=provider)
                        services.append(service_data)
                    booking.service.set(services)
        except Exception as e:
            raise serializers.ValidationError(f"Error creating booking: {str(e)}")
        return booking


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


        


