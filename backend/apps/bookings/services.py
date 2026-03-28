from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Bookings, ProviderModel, PaymentRequestBooking
from ..notification.events import NotificationEvents
from ..notification.services import send_general_notification
from apps.wallet.services import WalletService, lock_booking, refund_booking

from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from asyncio.log import logger

from ..wallet.transactions.models import Transactions
from ..wallet.transactions.services import get_or_create_transaction

User = get_user_model()

class BookingService:
    @staticmethod
    def release_funds(payment_request_instance, idempotency_key):
        try:
            with transaction.atomic():
                amount_to_transfer = 0
                amount = payment_request_instance.amount
                lock_balance = payment_request_instance.booking.locked

                if payment_request_instance.payment_type == \
                    PaymentRequestBooking.PaymentType.PART_TIME:

                    if lock_balance.amount < amount:
                        raise ValidationError("Payout amount is invalid")
                    if lock_balance.is_released:
                        raise ValidationError("This Payment had been released")

                    amount_to_transfer = amount
                    lock_balance.amount -= amount
                    lock_balance.save()

                else:
                    if lock_balance.is_released:
                        raise ValidationError("this payment had been released and closed")
                    if lock_balance != amount:
                        raise ValidationError("full payout requires requires full payment")

                    amount_to_transfer = lock_balance.amount
                    lock_balance.is_released = True
                    payment_request_instance.booking.booking_status = Bookings.BookingStatus.COMPLETED
                    payment_request_instance.booking.save()

                lock_balance.save()
                user = payment_request_instance.provider.profile.user
                payment_send = WalletService().credit_user_wallet(user, amount_to_transfer)
                transaction_instance = get_or_create_transaction(
                    idempotency_key=idempotency_key, sender=payment_request_instance.customer,
                    receiver=payment_request_instance.provider.profile.user, model=payment_request_instance.booking,
                    amount=amount_to_transfer,
                    type=Transactions.Type.RELEASE
                )
        except Exception as e:
            raise ValidationError(f"Error processing payment: {str(e)}")

    @staticmethod
    def create_booking(customer, provider, **validated_data):
        idempotency_key = validated_data.pop('idempotency_key')
        with transaction.atomic():
            booking = Bookings.objects.create(customer=customer, provider=provider, 
                                             **validated_data)
            # deduct user wallet under the same atomicity, is either the booking is
            # created and user wallet deducted or everything fails
            amount = booking.price
            deduct_balance = WalletService().deduct_user_balance(customer, amount)
            lock_deducted_balance = lock_booking(booking=booking)

            if not lock_deducted_balance.is_released:
                booking.booking_status = Bookings.BookingStatus.FUNDED
                transaction_instance = get_or_create_transaction(
                    idempotency_key=idempotency_key, sender=customer,
                    receiver=provider.profile.user, model=booking,
                    amount=lock_deducted_balance.amount,
                    type=Transactions.Type.ESCROW_HOLD,
                )
            booking.save()
        return  booking

    @staticmethod
    def cancel_booking(booking, user, idempotency_key):

        if not isinstance(booking, Bookings) or  not isinstance(user, User):
            raise ValidationError("Failed: 'booking' and 'user' should be valid instances")
    
        booking_pk = booking.pk
        with transaction.atomic():
            reverse_funds = refund_booking(booking=booking)
            # reverse user customer money under the same atomicity
            if reverse_funds.is_released:
                # create transaction
                transaction_instance = get_or_create_transaction(
                    idempotency_key=idempotency_key, model=booking,
                    sender=user, receiver=booking.customer,
                    type=Transactions.Type.REFUND, amount=reverse_funds.amount,
                    status=Transactions.Status.COMPLETED
                )
                booking = booking.cancel_booking(user=user)
                
        message = f"Your booking has been cancelled by {user.get_username()}."
        logger.info(f"Booking {booking_pk} cancelled by user {user.get_username()}.")
        send_general_notification(
            event=NotificationEvents.BOOKING.value,
            message=message,
            sender=user,
            receiver=booking.provider.profile.user if user == booking.customer else booking.customer
        )


    @staticmethod
    def accept_booking(booking, user):
        if not isinstance(booking, Bookings) and  not isinstance(user, User):
            raise ValidationError("Failed: 'booking' and 'user' should ba valid instances")

        with transaction.atomic():
            booking.accept_booking(user=user)

        booking_message = f"Booking {booking.pk}: Accepted {booking.provider.profile.user.username}."
        send_general_notification(
            event=NotificationEvents.BOOKING.value,
            message=booking_message,
            sender=booking.provider.profile.user,
            receiver=booking.customer
        )
        return booking

    @staticmethod
    def customer_and_provider_view(user, queryset):
        if queryset is None:
            return 0
        try:
            provider_profile = ProviderModel.objects.get(profile=user.profile)
            queryset = queryset.filter(provider=provider_profile)
        except ProviderModel.DoesNotExist:
            queryset = queryset.filter(customer=user)
        return queryset
    
    @staticmethod
    def delete_booking(booking, user):
        if not booking.is_participants(user):
            raise PermissionDenied()

        booking.soft_delete()


        


        
        
