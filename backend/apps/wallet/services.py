
from django.forms import ValidationError
from django.db import transaction, DatabaseError

from .models import User, Wallet, LockedWallet, BankAccount
from ..bookings.models import Bookings

from decimal import Decimal

@transaction.atomic
def lock_booking(booking, amount):
    if not isinstance(booking, Bookings):
        raise ValidationError("Not a valid booking instance")

    amount = amount

    wallet_to_lock = booking.customer.wallet
    if wallet_to_lock is None:
        raise ValidationError("customer wallet cannot be empty")

    lock = LockedWallet.objects.create(user_wallet=wallet_to_lock, booking=booking, 
                                       amount=amount, mutable_amount=amount - booking.platform_fee)

    if not lock.is_released:
        return lock
    raise ValidationError("Failed to lock booking payment")

@transaction.atomic
def refund_booking(booking, amount):

    locked_wallet = booking.locked

    if locked_wallet.is_released:
        raise ValidationError("payment already released")
    
    if locked_wallet.amount != amount:
        raise ValidationError("Price mismatch. can't release inconsistent pricing")
    
    user_to_credit = locked_wallet.booking.customer
    credit_wallet = WalletService().credit_user_wallet(user_to_credit, amount)

    locked_wallet.is_released = True
    locked_wallet.save(update_fields=['is_released'])
    return locked_wallet

def get_calculated_transaction(booking: Bookings):
    """ return the calcucated balance to send to provider( ie minus platform transaction fee)"""
    locked_wallet = booking.locked
    return locked_wallet.mutable_amount

class WalletService:

    @staticmethod
    def deduct_user_balance(user, amount):

        user_wallet = user.wallet

        if not user_wallet:
            raise ValidationError("no wallet instance for user")
        
        user_wallet.balance -= Decimal(amount)
        user_wallet.save(update_fields=["balance"])

        return user_wallet

    @staticmethod
    def credit_user_wallet(user, amount):
        user_wallet = user.wallet

        if not user_wallet: 
            raise ValidationError("no wallet instance for user")
        
        user_wallet.balance += Decimal(amount)
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


class BankAccountService:

    def __init__(self):
        pass

    def get_account_by_account_number(self, account_number):
        if account_number is None:
            return {"status": False, "message": "account number must be present"}
        
        try:
            bank_account = BankAccount.objects.get(account_number=account_number)
        except BankAccount.DoesNotExist:
            return {"status": False, "message": "bank account does not exists"}
        return {"status": True, "instance": bank_account}

    
    def get_account_by_recipient_code(self, recipient_code):
        if recipient_code is None:
            return {"status": False, "message": "account number must be present"}
        
        try:
            bank_account = BankAccount.objects.get(recipient_code=recipient_code, is_active=True)
        except BankAccount.DoesNotExist:
            return {"status": False, "message": "bank account does not exists"}
        return {"status": True, "instance": bank_account}