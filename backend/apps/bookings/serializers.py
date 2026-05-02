from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, NotFound

from ..core.utils.py import get_or_none
from ..users.address.models import UserAddress
from ..users.address.serializers import AddressCreateSerializer, AddressSerializer
from .models import Bookings, BookingAttachments, PaymentRequestBooking,\
BookingTransaction

from .helpers import is_customer
from .services import BookingService
from ..authentication.serializers import UserReadSerializer
from apps.wallet.services import WalletService
from ..wallet.services import get_calculated_transaction
from ..ratings.services.reviews import ReviewService



from decimal import Decimal
import logging


from ..users.provider_models import ProviderModel
from ..users.serializers.profiles import ProviderProfileDetailSerializer, ProviderProfilePublicSerializer

logger = logging.getLogger(__name__)

class BookingAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingAttachments
        fields = [
            'attachment_type_booking', 'attachmentURL_booking',
        ]

class BookingCreateSerializer(serializers.ModelSerializer):
    address = AddressCreateSerializer(required=True)
    provider_id = serializers.UUIDField(required=True)
    attachments = BookingAttachmentSerializer(many=True, required=False)
    idempotency_key = serializers.UUIDField(required=True)

    class Meta:
        model = Bookings
        fields = [
            'address',
            "provider_id",
            "price", "notes",
            "descriptions", "start_date",
            "end_date", "currency",
            "requirements", 'attachments', 'idempotency_key'
        ]

    def validate(self, attrs):
        if attrs.get("start_date") or attrs.get("end_date"):

            if attrs["end_date"] <= attrs["start_date"]:
                raise serializers.ValidationError("'end_date' cannot be less than 'start_date'")
            elif attrs["start_date"].date() < timezone.now().date():
                raise serializers.ValidationError("invalid start date. can't be less than today")

        return attrs

    def validate_price(self, value):
        request = self.context['request']

        wallet = WalletService.get_user_wallet(user=request.user)
        main_balance = wallet.balance
        if main_balance is None:
            raise serializers.ValidationError("User wallet has no balance")

        if Decimal(value) > Decimal(main_balance):
            raise serializers.ValidationError("Insufficient Balance. Top up to continue")

        return value

    def create(self, validated_data):
        request = self.context['request']

        if not is_customer(request):
            raise serializers.ValidationError("User is not a customer")

        provider_pk = validated_data['provider_id']
        provider_profile = get_or_none(ProviderModel, pk=provider_pk)

        if provider_profile is None:
            raise NotFound("profile not found for provider")

        address = validated_data.pop("address", None)
        attachment = validated_data.pop("attachments", None)
        validated_data.pop("provider_id")

        if address is not None:
            postal_code = address.pop('postal_code')
            address, created = UserAddress.objects.get_or_create(
                user_profile=request.user.profile,
                postal_code=postal_code,
                **address
            )

        booking_instance = BookingService().create_booking(
            customer=request.user, provider=provider_profile,
            **validated_data
        )

        if attachment is not None:
            BookingAttachments.objects.bulk_create([
                BookingAttachments(booking=booking_instance, **data)
                for data in attachment
            ])

        booking_instance.address = address
        booking_instance.save()

        return booking_instance

    @transaction.atomic
    def update(self, instance: Bookings, validated_data):
        address = validated_data.pop("address", None)
        attachments = validated_data.pop("attachments", None)
        user = self.context['request'].user
        if address:
            booking_address, _ = UserAddress.objects.get_or_create(profile=user.profile, postal_code=address['postal_code'])
            instance.address = booking_address

        if attachments:
            instance.attachments.all().delete()
            BookingAttachments.objects.bulk_create([
                BookingAttachments(booking=instance, **data)
                for data in attachments
            ])

        validated_data.pop('idempotency_key')
        validated_data.pop("provider_id")

        updated_instance = super().update(instance, validated_data)
        return updated_instance

class AcceptRejectSerializer(serializers.Serializer):
    choices = ['ACCEPT', 'REJECT']

    status = serializers.ChoiceField(choices=choices, required=True)
    idempotency_key = serializers.UUIDField(required=True)
    booking_id = serializers.UUIDField(required=True)

    def validate_status(self, value):
        if value.upper() not in self.choices:
            raise serializers.ValidationError("Bad Request. status is not in active choices")
        return value

    def create(self, validated_data):
        choice = validated_data['status']
        idempotency_key = validated_data['idempotency_key']
        booking_instance_pk = validated_data['booking_id']

        instance = get_or_none(Bookings, pk=booking_instance_pk,
                               is_active=True, booking_status=Bookings.BookingStatus.FUNDED)

        if instance is None:
            raise serializers.ValidationError("No booking found. Try requesting for a funded booking")

        user = self.context['request'].user

        if not instance.is_participants(user):
            raise PermissionDenied()

        if choice == self.choices[0]:
            # accept booking
            if user != instance.provider.profile.user:
                raise PermissionDenied()
            
            booking = BookingService().accept_booking(instance, user)
            if booking.booking_status != Bookings.BookingStatus.IN_PROGRESS:
                raise serializers.ValidationError("Booking did not update")
            
        elif choice == self.choices[1]:
            # reject/cancel booking
            booking = BookingService().cancel_booking(
                booking=instance, user=user, idempotency_key=idempotency_key)
            
            if booking.booking_status != Bookings.BookingStatus.CANCELLED:
                raise serializers.ValidationError("Booking cancel not updated")
        else:
            raise serializers.ValidationError("Future update coming")

        return booking

class BookingSerializer(serializers.ModelSerializer):
    customer = UserReadSerializer(read_only=True)
    provider = ProviderProfilePublicSerializer(read_only=True)
    class Meta:
        model = Bookings
        fields =[
            'booking_id', 'booking_status',
            'customer', 'provider',
            'price', "descriptions",
            'is_active', 'start_date', 'end_date',
            'created_at',
        ]

class BookingDetailSerializer(serializers.ModelSerializer):

    customer = UserReadSerializer(read_only=True)
    provider = ProviderProfileDetailSerializer(read_only=True)
    cancelled_by = UserReadSerializer(read_only=True)
    accepted_by = UserReadSerializer(read_only=True)

    class Meta:
        model = Bookings
        fields = [
            'booking_id', 'booking_status',
            'customer', 'provider',
            'cancelled_by', 'accepted_by',
            'price', 'notes', 'requirements',
            'is_active', 'start_date', 'end_date',
            'created_at', 'cancelled_at', 'accepted_at',
            'descriptions', 'currency'
        ]

class PaymentRequestSerializer(serializers.ModelSerializer):

    attachments_payment_request = BookingAttachmentSerializer(many=True, required=True)
    booking_id = serializers.UUIDField(required=True, write_only=True)

    class Meta:
        model = PaymentRequestBooking
        fields = [
            'booking_id', 'attachments_payment_request',
            'amount', 'message', 'payment_type'
        ]

    def validate_message(self, value):
        return value.strip()
    
    def validate(self, data):

        booking_pk = data['booking_id']

        booking_instance = get_or_none(
            Bookings, pk=booking_pk,
            booking_status=Bookings.BookingStatus.IN_PROGRESS)
 
        if booking_instance is None:
            raise serializers.ValidationError("invalid request")

        user = self.context['request'].user
        
        if not booking_instance.is_participants(user):
            raise PermissionDenied()

        payment_instance = booking_instance.locked

        provider_total_payout = get_calculated_transaction(booking=booking_instance)

        if payment_instance.is_released:
            raise serializers.ValidationError("payment already released and closed")

        if data['payment_type'] == PaymentRequestBooking.PaymentType.PART_TIME and \
            data['amount'] > provider_total_payout / 2:

            raise serializers.ValidationError("Part payment cannot be greater than half of the full payment")
        
        if data['payment_type'] == PaymentRequestBooking.PaymentType.FULL_TIME and \
            data['amount'] != provider_total_payout:
            
            raise serializers.ValidationError('please request full payout on full payment')

        if provider_total_payout < data['amount']:
            raise serializers.ValidationError('invalid_digits_amounts')
        
        data['booking_instance'] = booking_instance
        data['locked_wallet'] = payment_instance

        return data

    def create(self, validated_data):
        attachments = validated_data.pop("attachments_payment_request", None)

        user = self.context['request'].user

        booking_instance =  validated_data.pop('booking_instance')
        locked_wallet = validated_data.pop('locked_wallet')

        latest_payout_request  = (
            PaymentRequestBooking.objects.filter(booking=booking_instance)
            .select_related("booking", "provider", "customer")
            .order_by("-requested_at")
            .first()
        )

        if latest_payout_request is not None:
            duration = latest_payout_request.requested_at + timezone.timedelta(hours=24)
            if duration > timezone.now():
                next_payout = duration - timezone.now()
                hours_left = next_payout.total_seconds() // 3600

                raise serializers.ValidationError(
                    f"Request under review. request will be open in {hours_left} hour(s)" 
                )

        if booking_instance.provider.profile.user != user:
            raise PermissionDenied()
        
        amount = validated_data.pop("amount")

        payment_request_instance = PaymentRequestBooking.objects.create(
            provider=booking_instance.provider, customer=booking_instance.customer,
            booking=booking_instance, amount=amount, **validated_data
        )

        if attachments:
            BookingAttachments.objects.bulk_create([
                BookingAttachments(payment_request=payment_request_instance, **data)
                for data in attachments
            ]
            )

        return payment_request_instance

class ReviewPaymentRequestSerializer(serializers.ModelSerializer):
    choices = ['ACCEPT', 'REJECT']

    idempotency_key = serializers.UUIDField(write_only=True, required=True)
    action = serializers.ChoiceField(choices=choices, required=True)
    request_id = serializers.UUIDField(required=True, write_only=True)
    ratings = serializers.IntegerField(max_value=5, min_value=1,  required=False)
    reviews = serializers.CharField(max_length=500, required=False)

    class Meta:
        model = PaymentRequestBooking
        fields = [
            'action', 'request_id',
            'idempotency_key', 'ratings',
            'reviews'
        ]

    def validate(self, data):
        user = self.context['request'].user

        request_instance  = (
            PaymentRequestBooking.objects.filter(pk=data['request_id'])
            .select_related("booking", "provider", "customer")
            .order_by("-requested_at")
            .first()
        )

        if request_instance is None:
            raise serializers.ValidationError("payment request not found")

        if user != request_instance.customer:
            raise PermissionDenied()

        if request_instance.status != PaymentRequestBooking.RequestStatus.PENDING:
            raise serializers.ValidationError("You can only review pending request")

        data['payment_request'] = request_instance

        return data

    def create(self, validated_data):

        idempotency_key = validated_data['idempotency_key']
        request_instance = validated_data['payment_request']
        action = validated_data['action']
        
        if "ratings" in validated_data or "reviews" in validated_data:
            provider = request_instance.provider
            customer = request_instance.customer

            ratings = validated_data.get("ratings", None)
            reviews = validated_data.get("reviews", None)

            data = {
                "reviews": reviews,
                "provider_profile": provider,
                "reviewed_by": customer,
                "ratings": ratings
            }
            review_service = ReviewService()
            if review_service._dublicate_reviews(customer, provider):
                raise serializers.ValidationError("review found for this user")

            if review_service._cant_review_yourself(customer, provider):
                raise serializers.ValidationError("You cannot review yourself.")

            review_instance = review_service.create_review(data)
            
        if action == self.choices[1]:
            request_instance.status = PaymentRequestBooking.RequestStatus.REJECTED
        else:
            release = BookingService().release_funds(request_instance, idempotency_key)
            request_instance.status = PaymentRequestBooking.RequestStatus.APPROVED

        request_instance.reviewed_at = timezone.now()
        request_instance.save()

        return request_instance

class RequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentRequestBooking
        
        fields = [
            'request_id', 'message',
            'amount', 'booking',
            'provider', 'customer',
            'status', 'requested_at',
            'reviewed_at'
        ]

class PaymentRequestDetailSerializer(serializers.ModelSerializer):
    customer = UserReadSerializer(read_only=True)
    provider = ProviderProfileDetailSerializer(read_only=True)
    booking = BookingDetailSerializer(read_only=True)
    attachments_payment_request = BookingAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = PaymentRequestBooking

        fields = [
            'request_id', "booking",
            'message', 'amount',
            'payment_type', 'status',
            'requested_at', 'updated_at',
            'reviewed_at', 'customer', 'provider',
            'attachments_payment_request'

        ]

class BookingTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingTransaction
        fields = [
            "transaction_id"
        ]