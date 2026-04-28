from django.db import transaction
from django.utils import timezone

from ..models import WalletTransaction
from ..exceptions import DuplicateTransactionError
from ..services import WalletService

class WalletTransactionService:

    def create_wallet_transaction(self, amount, user, wallet, **validated_data):

        try:
            if WalletTransaction.objects.filter(idempotency_key=validated_data['idempotency_key']).first():
                raise DuplicateTransactionError()

            with transaction.atomic():
                wallet_transaction = WalletTransaction.objects.create(
                    amount=amount, user=user, wallet=wallet,
                    **validated_data
                )
        except DuplicateTransactionError as e:
            return {"status": False, "transaction": None, "reason": str(e)}
        except Exception as e:
            return {"status": False, "transaction": None, 'reason': f"{str(e)}"}
        
        return {"status": True, "transaction": wallet_transaction}
    

    def process_completed_withdrawal(self, withdrawal):
        if not isinstance(withdrawal, WalletTransaction):
            return { "status": False, "message": "not a valid with drawal instance"}
        
        try:
            withdrawal.status = WalletTransaction.Status.COMPLETED
            withdrawal.completed_at = timezone.now()

            withdrawal.save(update_fields=['status', 'completed_at'])
        except Exception as exc:
            return { "status": False, "message": "Failed to process complted withdrawal"}

        return withdrawal
    
    def process_failed_withdrawal(self, withdrawal):
        if not isinstance(withdrawal, WalletTransaction):
            return { "status": False, "message": "not a valid with drawal instance"}
        
        try:
            withdrawal.status = WalletTransaction.Status.FAILED
            withdrawal.failed_at = timezone.now()

            wallet_service = WalletService()
            wallet_service.credit_user_wallet(withdrawal.wallet.user, withdrawal.amount)

            withdrawal.save(update_fields=['status', 'failed_at'])
        except Exception as exc:
            return { "status": False, "message": "Failed to process failed withdrawal"}

        return withdrawal




