from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Bookings, ProviderModel, PaymentRequestBooking, BookingTransaction
from ..notification.events import NotificationEvents
from .exceptions import DuplicateBookingError
from ..notification.services import send_general_notification
from .booking_transaction import process_transaction
from apps.wallet.services import WalletService, lock_booking, refund_booking, get_calculated_transaction

from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from asyncio.log import logger

User = get_user_model()

class BookingService:

    @staticmethod
    def release_funds(payout_request_instance: PaymentRequestBooking, idempotency_key):

        transaction_status = False
        amount = payout_request_instance.amount
        payout_type = payout_request_instance.payment_type

        booking = payout_request_instance.booking

        locked_wallet = booking.locked

        if locked_wallet.is_released:
            raise ValidationError("payment has already been released and closed")
        
        total_provider_funds = get_calculated_transaction(booking=booking)
        if total_provider_funds < amount:
                raise ValidationError("Payout amount is invalid")
        
        try:
            with transaction.atomic():
                if payout_type == \
                    PaymentRequestBooking.PaymentType.PART_TIME:
                    locked_wallet.mutable_amount -= amount

                    amount_to_transfer = amount

                else:
                    amount_to_transfer = total_provider_funds
                    locked_wallet.mutable_amount -= amount_to_transfer
                    
                    locked_wallet.is_released = True
                    
                locked_wallet.save()
                user = booking.provider.profile.user

                credit_provider = WalletService().credit_user_wallet(user, amount_to_transfer)
                
                booking.booking_status = Bookings.BookingStatus.COMPLETED
                booking.save()
                transaction_status = True
        except Exception as e:
            transaction_status = False
            logger.exception(f"Error processing payment: {str(e)}", exc_info=True)

        transaction.on_commit(lambda: process_transaction(
                booking_id=booking.pk, action=BookingTransaction.Type.RELEASE, 
                idempotency_key=idempotency_key, status=transaction_status
            ))
        

    @staticmethod
    def create_booking(customer, provider, **validated_data):
        idempotency_key = validated_data.pop('idempotency_key')
        if BookingTransaction.objects.filter(idempotency_key=idempotency_key).exists():
            raise DuplicateBookingError()
        
        booking = None
        transaction_status = False
        
        with transaction.atomic():
            try:
            
                booking = Bookings.objects.create(customer=customer, provider=provider, 
                                                **validated_data)
                # deduct user wallet under the same atomicity, is either the booking is
                # created and user wallet deducted or everything fails
                booking_price = booking.price

                booking_fee = Bookings().get_booking_fee(amount=booking_price)
                booking.platform_fee = booking_fee
                booking.save()
                
                deduct_balance = WalletService().deduct_user_balance(customer, booking_price)
            
                lock_deducted_balance = lock_booking(booking=booking, amount=booking_price)

                if not lock_deducted_balance.is_released:
                    booking.booking_status = Bookings.BookingStatus.FUNDED

                
                transaction_status = True  # Mark as successful only if everything succeeds
                
            except Exception as e:
                logger.exception(f"Failed to create booking: {e}", exc_info=True)
                transaction_status = False

            if booking:
                process_transaction(
                    booking_id=booking.pk, action=BookingTransaction.Type.ESCROW_HOLD, 
                    idempotency_key=idempotency_key, status=transaction_status
                )
            
        return booking

    @staticmethod
    def cancel_booking(booking, user, idempotency_key):

        if not isinstance(booking, Bookings) or  not isinstance(user, User):
            raise ValidationError("Failed: 'booking' and 'user' should be valid instances")

        transaction_status = False

        with transaction.atomic():
            try:
                cancel = booking.cancel_booking(user=user)

                amount_to_refund = booking.price
             
                # refund customer funds 
                reverse_funds = refund_booking(booking=booking, amount=amount_to_refund)
                
                if reverse_funds.is_released:
                    # create transaction
                    transaction_status = True
            except Exception as e:
                logger.exception(f"Failed to reverse booking: {e}", exc_info=True)
                transaction_status = False
            
        transaction.on_commit( lambda: process_transaction(
                booking_id=booking.pk, action=BookingTransaction.Type.REFUND,
                idempotency_key=idempotency_key, status=transaction_status
                ))

        message = f"Your booking has been cancelled by {user.full_name}."
        logger.info(f"Booking {booking.pk} cancelled by user {user.get_username()}.")

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

    @staticmethod
    def fetch_rewarded_booking():

        try:
            bookings = Bookings.objects\
                        .select_related("customer", "provider", "address", "cancelled_by", "accepted_by")\
                        .filter(booking_status=Bookings.BookingStatus.COMPLETED)\
                        .only("booking_status", 'provider', 'customer', 'booking_id', "address")
            return bookings
        except Exception as e:
            raise
            


        


        
        
