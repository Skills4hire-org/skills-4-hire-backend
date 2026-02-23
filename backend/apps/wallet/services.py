
from asyncio.log import logger

from django.forms import ValidationError
from django.db import transaction, DatabaseError


from .models import User, Wallet, LockedWallet


class WalletService:
    @staticmethod
    def get_user_wallet(user):
        if not user.is_authenticated:
            raise ValidationError("User must be authenticated to access wallet.")
        try:
            return user.wallet
        except Wallet.DoesNotExist:
            raise ValidationError("Wallet does not exist for the user.")    
        
    
    @staticmethod
    def lock_booking_payment(customer_wallet, amount, booking):
        """ 
        A simple funtion for locking provider payment until work is completed
        """
        if customer_wallet.main_balance < amount:
            raise ValidationError("Insufficient balance to lock payment for provider.")
        try:
            with transaction.atomic():
                LockWalletService.lock_payment(customer_wallet, amount, booking.provider)
                logger.info(f"Locked payment of {amount} for provider. Customer wallet debited by {amount}.")
        except DatabaseError:
            logger.exception("Failed to lock provider payment due to a database error.")
            raise DatabaseError("Failed to lock provider payment due to a database error.")
        except Exception as e:
            logger.exception(f"Failed to lock provider payment due to an unexpected error: {str(e)}")
            raise ValidationError("Failed to lock provider payment due to an unexpected error.")
        
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
        

class LockWalletService:

    @transaction.atomic()
    @staticmethod
    def lock_payment(customer_wallet: Wallet, amount: float | int, provider = None) -> LockedWallet:
        try:
            locked_payment = LockedWallet(
                wallet=customer_wallet, 
                amount=amount, 
            )

            if provider is not None:
                locked_payment.provider = provider
            else :
                locked_payment.provider = None
            locked_payment.save()
        except Exception:
            raise Exception("Error locking booking payment")
        return locked_payment

