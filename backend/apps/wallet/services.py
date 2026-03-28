
from asyncio.log import logger

from django.forms import ValidationError
from django.db import transaction, DatabaseError

from .models import User, Wallet, LockedWallet
from ..bookings.models import Bookings

def lock_booking(booking):
    if not isinstance(booking, Bookings):
        raise ValidationError("Not a valid booking instance")

    amount = booking.price
    wallet_to_lock = booking.customer.wallet
    if wallet_to_lock is None:
        raise ValidationError("customer wallet cannot be empty")

    if wallet_to_lock.balance < amount:
        raise ValidationError("Insufficient funds")
    lock = LockedWallet.objects.create(user_wallet=wallet_to_lock, booking=booking, amount=amount)

    if not lock.is_released:
        return lock
    raise ValidationError("Failed to lock booking payment")

def refund_booking(booking):

    locked = booking.locked
    if locked.is_released:
        raise ValidationError("payment already released")
    amount = locked.amount
    user = locked.booking.customer

    credit_wallet = WalletService().credit_user_wallet(user, amount)
    locked.is_released = True
    locked.save(update_fields=['is_released'])
    return locked

class WalletService:

    @staticmethod
    def deduct_user_balance(user, amount):

        user_wallet = user.wallet
        if not user_wallet:raise ValidationError("no wallet instance for user")
        user_wallet.balance -= amount
        user_wallet.save(update_fields=["balance"])

        return user_wallet

    @staticmethod
    def credit_user_wallet(user, amount):
        user_wallet = user.wallet
        if not user_wallet: raise ValidationError("no wallet instance for user")
        user_wallet.balance += amount
        user_wallet.save(update_fields=["balance"])

        return user_wallet

    @staticmethod
    def get_user_wallet(user):
        if not user.is_authenticated:
            raise ValidationError("User must be authenticated to access wallet.")
        try:
            return user.wallet
        except Wallet.DoesNotExist:
            raise ValidationError("Wallet does not exist for the user.")    

    @staticmethod
    def create_wallet(user):
        if not isinstance(user, User):
            raise ValidationError("'user' is not a valid 'CustomUser' instance")
        try:
            with transaction.atomic():
                wallet = Wallet.objects.create(user=user)
                return wallet
        except DatabaseError:
            raise DatabaseError("Failed to create wallet due to a database error.")
        except Exception:
            raise ValidationError("Failed to create wallet due to an unexpected error.")
